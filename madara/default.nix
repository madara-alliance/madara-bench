#    __  __           _                   _____
#   |  \/  |         | |                 |_   _|
#   | \  / | __ _  __| | __ _ _ __ __ _    | |  _ __ ___   __ _  __ _  ___
#   | |\/| |/ _` |/ _` |/ _` | '__/ _` |   | | | '_ ` _ \ / _` |/ _` |/ _ \
#   | |  | | (_| | (_| | (_| | | | (_| |  _| |_| | | | | | (_| | (_| |  __/
#   |_|  |_|\__,_|\__,_|\__,_|_|  \__,_| |_____|_| |_| |_|\__,_|\__, |\___|
#                      ____        _ _     _                     __/ |
#                     |  _ \      (_) |   | |                   |___/
#                     | |_) |_   _ _| | __| | ___ _ __
#                     |  _ <| | | | | |/ _` |/ _ \ '__|
#                     | |_) | |_| | | | (_| |  __/ |
#                     |____/ \__,_|_|_|\__,_|\___|_|
#
# ---
# Builder which generates the Madara Node docker image for use in benchmarking.
# Run with `nix-build`. This will generate an installation script as
# `./result/bin/copyto` which can then be executed to bring the generate docker
# image `.tar.gz` into the current directory. This can then be loaded into
# docker using `docker load -i image.tar.gz`.
# ---
with import <nixpkgs>
{
  overlays = [
    (import (fetchTarball "https://github.com/oxalica/rust-overlay/archive/master.tar.gz"))
  ];
}; let
  rustPlatform = makeRustPlatform {
    cargo = rust-bin.nightly."2024-05-31".minimal;
    rustc = rust-bin.nightly."2024-05-31".minimal;
  };

  cairoVersion = "2.8.2";

  # The version of Madara being used
  # Updating this might also cause other nix hashes to need to be re-specified.
  madaraSrc = fetchFromGitHub {
    owner = "madara-alliance";
    repo = "madara";
    rev = "a0fa067eea3e00dd8c994a8ad0c62004695df3b3";
    sha256 = "sha256-c1vQA6qi+KmGii2nvDiJcY3Al8eAR5crCy4cfwoUhO0=";
  };

  # Building madara with nix
  # https://ryantm.github.io/nixpkgs/languages-frameworks/rust/
  madara = rustPlatform.buildRustPackage rec {
    pname = "madara";
    version = "latest";

    src = madaraSrc;

    cargoLock = {
      lockFile = madaraSrc + "/Cargo.lock";
      allowBuiltinFetchGit = true;
    };

    nativeBuildInputs = with pkgs; [
      pkg-config
      protobuf
      openssl
      clang
    ];

    buildInputs = with pkgs; [
      openssl
    ];

    stripAllFlags = ["--strip-all" "--remove-section=.comment" "--remove-section=.note"];
    # allowedReferences = ["out"];

    # This will currently fail due to how scarb is used in the codebase,
    # resulting in an impure build which requires network access to download
    # dependencies during the build step. It seems the only way to fix this
    # would be to make upstream changes to scarb to allow pre-feching
    # dependencies and making them available to scarb
    #
    # Current workaround is to rely on a simpler but less reproducible and
    # performant Dockerfile
    buildType = "production";

    # Tests are disabled as we assume we are already using a working version
    doCheck = false;

    # clang does not correctly update its path in nix and so we need to patch it
    # manually
    preBuild = ''
      export LIBCLANG_PATH=${llvmPackages.libclang.lib}/lib
    '';
  };

  minimal-madara = stdenv.mkDerivation {
    name = "minimal-madara";

    # Only need the original binary as input
    src = madara;

    nativeBuildInputs = [upx];

    buildPhase = ''
      cp $src/bin/madara madara
      chmod +w madara
      upx --best madara
    '';

    installPhase = ''
      mkdir -p $out/bin
      cp madara $out/bin/
      chmod +x $out/bin/madara
    '';
  };

  # This is necessary to avoid 'unable to get local issuer certificate'
  # https://discourse.nixos.org/t/adding-a-new-ca-certificate-to-included-bundle/14301/8
  minimal-cacert = stdenv.mkDerivation {
    name = "minimal-cacert";
    buildInputs = [cacert];
    buildCommand = ''
      mkdir -p $out/etc/ssl/certs
      cp ${cacert}/etc/ssl/certs/ca-bundle.crt $out/etc/ssl/certs/
    '';
  };

  minimal-stdcpp = stdenv.mkDerivation {
    name = "minimal-stdcpp";
    phases = ["installPhase"];
    installPhase = ''
      mkdir -p $out/lib
      cp ${stdenv.cc.cc.lib}/lib/libstdc++.so.6 $out/lib/
    '';
  };

  minimal-ssl = stdenv.mkDerivation {
    name = "minimal-ssl";
    phases = ["installPhase"];
    installPhase = ''
      mkdir -p $out/lib
      cp ${openssl.out}/lib/libssl.so $out/lib/
    '';
  };
  # # Additional images can be downloaded with `docerTools.pullImage`
  # debian = dockerTools.pullImage {
  #   imageName = "debian";
  #   imageDigest = "sha256:b8084b1a576c5504a031936e1132574f4ce1d6cc7130bbcc25a28f074539ae6b";
  #   sha256 = "sha256-iCIQnlHMPmkjw4iDdwU5Da4udYjYl0tmUqj16za0xhU=";
  # };
in
  # Generates docker image using nix. This is equivalent to using `FROM scratch`.
  # https://ryantm.github.io/nixpkgs/builders/images/dockertools/
  dockerTools.buildImage {
    name = "madara";
    tag = "latest";

    # Use `fromImage` to specify a base image. This image must already be
    # available locally, such as after using `dockerTools.pullImage`
    # fromImage = debian;

    copyToRoot = pkgs.buildEnv {
      name = "madara";
      paths = [
        minimal-madara
        minimal-cacert
        minimal-stdcpp
        minimal-ssl
      ];
      pathsToLink = ["/bin" "/etc" "/lib"];

      postBuild = ''
        mv $out/bin/madara $out/bin/madara.link
        mv $out/lib/libssl.so $out/lib/libssl.so.link
        mv $out/lib/libstdc++.so.6 $out/lib/libstdc++.so.6.link

        cp -L $out/bin/madara.link $out/bin/madara
        cp -L $out/lib/libssl.so.link $out/lib/libssl.so
        cp -L $out/lib/libstdc++.so.6.link $out/lib/libstdc++.so.6

        rm $out/bin/madara.link
        rm $out/lib/libssl.so.link
        rm $out/lib/libstdc++.so.6.link
      '';
    };

    config = {
      EntryPoint = ["/bin/madara"];
      Cmd = ["--help"];
      Env = [
        "SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt"
      ];
    };
  }
