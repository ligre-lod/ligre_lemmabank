{
  inputs.nixpkgs.url = "github:Nixos/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {inherit system;};
      in {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            nodejs
            pnpm
            biome
          ];
        };
        packages = {
          default = pkgs.stdenv.mkDerivation (finalAttrs: {
            pname = "ligre-queryinterface-frontend";
            version = "0.1.0";
            src = ./.;
            buildInputs = with pkgs; [
              nodejs
              pnpm
              pnpm.configHook
            ];
            pnpmDeps = pkgs.pnpm.fetchDeps {
              inherit (finalAttrs) pname version src;
              hash = "sha256-HqpwQeE3Aef5Eoe+nn4A5nimsntzkgm1+Rc5EONFqYw=";
            };
            buildPhase = ''
              pnpm run build
            '';

            installPhase = ''
              cp -r dist $out
            '';
          });
        };
      }
    );
}
