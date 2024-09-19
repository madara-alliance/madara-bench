{
  description = "Madara node runner runtime dependencies";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        buildInputs = with pkgs; [
          python312
          poetry
          gnumake
          docker-compose
          stdenv
        ];
        ld_library = "export LD_LIBRARY_PATH=\"${pkgs.stdenv.cc.cc.lib}/lib\"";
        traps = "trap \"make stop && exit\" INT; trap \"make stop && exit\" QUIT;";
      in {
        devShells = {
          default = pkgs.mkShell {
            buildInputs = buildInputs;
            shellHook = ''
              ${ld_library}
            '';
          };

          start = pkgs.mkShell {
            buildInputs = buildInputs;
            shellHook = ''
              ${ld_library}
              ${traps}
              make start
            '';
          };

          restart = pkgs.mkShell {
            buildInputs = buildInputs;
            shellHook = ''
              ${ld_library}
              ${traps}
              make restart
            '';
          };

          frestart = pkgs.mkShell {
            buildInputs = buildInputs;
            shellHook = ''
              ${ld_library}
              ${traps}
              make frestart
            '';
          };

          help = pkgs.mkShell {
            buildInputs = buildInputs;
            shellHook = ''
              ${ld_library}
              make help
              exit
            '';
          };
        };
      }
    );
}
