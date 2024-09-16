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

  # Required to build scarb
  cairoArchive = fetchurl {
    name = "cairo-archive-${cairoVersion}";
    url = "https://github.com/starkware-libs/cairo/archive/v${cairoVersion}.zip";
    sha256 = "sha256-biuqlMHtm7Ub97O4HvujNx/RPWdZMxaoLvtv5or8v4U=";
  };

  scarbVersion = "2.8.2";

  # Scarb, the cairo package manager, used to run contracts for devenet
  # integration in the madara node
  scarbSrc = fetchFromGitHub {
    owner = "software-mansion";
    repo = "scarb";
    rev = "aaa5a5f74d20490a5f812a35a2705aeea3b55b68";
    hash = "sha256-1aE1vZvNEDmxT1tXwQDm5smFv2Yf434WaBC8rd5TYYQ=";
  };

  # Building scarb with nix
  scarb = rustPlatform.buildRustPackage rec {
    pname = "scarb";
    version = scarbVersion;

    src = scarbSrc;

    # This is neeed by a buildscript in scarb/utils/scarb-build-metadata/build.rs
    CARGO_MANIFEST_DIR = "${scarbSrc}";
    CARGO_PKG_NAME = "scarb";
    CAIRO_ARCHIVE = cairoArchive;

    cargoLock = {
      lockFile = scarbSrc + "/Cargo.lock";
      allowBuiltinFetchGit = true;
    };

    nativeBuildInputs = with pkgs; [
      pkg-config
      openssl
      clang
      perl
      cmake
    ];

    buildInputs = with pkgs; [
      openssl
    ];

    doCheck = false;

    preBuild = ''
      export LIBCLANG_PATH=${llvmPackages.libclang.lib}/lib
    '';
  };

  cairo-contracts = fetchgit {
    url = "https://github.com/openzeppelin/cairo-contracts";
    rev = "bac08ee8c47a87e4060d196bf30abc184930c247";
    sha256 = "sha256-GziEDo51Cl8XtD4o3OXb4Qn21R3eHTgCnPvY4GwXpV8=";
  };

  toTOML = pkgs.formats.toml {};

  # The version of Madara being used
  # Updating this might also cause other nix hashes to need to be re-specified.
  madaraSrc = fetchFromGitHub {
    owner = "madara-alliance";
    repo = "madara";
    rev = "9f11048d12e6198937ea47724a98adba42c25e84";
    sha256 = "sha256-ZRKZh6i1xV1AXEHeLpNZz+bU2RpCZnndNc9h9OZPr+w=";
  };

  # Building madara with nix
  # https://ryantm.github.io/nixpkgs/languages-frameworks/rust/
  madara = rustPlatform.buildRustPackage rec {
    pname = "madara";
    version = "latest";

    src = madaraSrc;

    SCARB_TARGET_DIR = madaraSrc + "/target";
    SCARB_CACHE = "/tmp/.cache/scarab";
    CAIRO_ARCHIVE = cairoArchive;

    cargoLock = {
      lockFile = madaraSrc + "/Cargo.lock";
      allowBuiltinFetchGit = true;
    };

    nativeBuildInputs = with pkgs; [
      pkg-config
      protobuf
      openssl
      clang
      scarb
    ];

    buildInputs = with pkgs; [
      openssl
    ];

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

  # # Additional images can be downloaded with `docerTools.pullImage`
  # debian = dockerTools.pullImage {
  #   imageName = "debian";
  #   imageDigest = "sha256:b8084b1a576c5504a031936e1132574f4ce1d6cc7130bbcc25a28f074539ae6b";
  #   sha256 = "sha256-iCIQnlHMPmkjw4iDdwU5Da4udYjYl0tmUqj16za0xhU=";
  # };

  # Creates a derivation of busybox with only `cat` and `du` accessible. This
  # avoids bloating our docker image with unnecessary dependencies. We use
  # busybox to shave of even more space with tiny implementation of these.
  # `cat` is used to retrieve mounted secrets
  # `du` is used to measure the size of the db
  util = stdenv.mkDerivation {
    name = "minimal-cat";
    buildInputs = [busybox];
    buildCommand = ''
      mkdir -p $out/bin
      cp ${busybox}/bin/cat $out/bin/
      cp ${busybox}/bin/du $out/bin/
    '';
  };

  runner = writeScriptBin "madara-runner" ''
    #!${pkgs.stdenv.shell}
    export RPC_API_KEY=$(cat $RPC_API_KEY_FILE)
    export GATEWAY_KEY=$(cat $GATEWAY_KEY_FILE)

    /bin/madara                  \
      --name madara              \
      --base-path /data/madara   \
      --network test             \
      --rpc-external             \
      --rpc-cors all             \
      --l1-endpoint $RPC_API_KEY \
      --gateway-key $GATEWAY_KEY
  '';

  # Generates docker image using nix. This is equivalent to using `FROM scratch`.
  # https://ryantm.github.io/nixpkgs/builders/images/dockertools/
  image = dockerTools.buildImage {
    name = "madara";
    tag = "latest";

    # # Use `fromImage` to specify a base image. This image must already be
    # # available locally, such as after using `dockerTools.pullImage`
    # fromImage = debian;

    copyToRoot = buildEnv {
      name = "madara";
      paths = [
        madara
        runner
        util
        # This is necessary to avoid 'unable to get local issuer certificate'
        # https://discourse.nixos.org/t/adding-a-new-ca-certificate-to-included-bundle/14301/8
        cacert
      ];
      pathsToLink = ["/bin"];
    };

    config = {
      Cmd = ["/bin/madara-runner"];
      Env = ["SSL_CERT_FILE=${cacert}/etc/ssl/certs/ca-bundle.crt"];
    };
  };
  # Calling `nix-build` on this file will create an artifact in `/nix/store/`.
  # Crucially, nix uses the default unix time as date of last modification. This
  # poses an issue since it means Make will always flag this output as
  # out-of-date.
  #
  # To avoid this, we create a script which copies the generated docker image to
  # a given directory, updating its date to the current time. We cannot do this
  # otherwise as only root has ownership of artifacts generated in `/nix/store/`.
  #
  # This way, we are able to guarantee that docker images will not be rebuilt by
  # Make on each run, along with any other command associated to their generation
  # such as `docker load -i`.
in
  writeScriptBin "copyto" ''
    #!${pkgs.stdenv.shell}
    cp ${image} $1
    touch -m $1
  ''
