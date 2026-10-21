{
  description = "Bruno's command-line development tools";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { nixpkgs, ... }:
    let
      system = "aarch64-darwin";
      pkgs = import nixpkgs { inherit system; };
    in {
      packages.${system}.default = pkgs.buildEnv {
        name = "personal-development-tools";
        paths = with pkgs; [
          nodejs_24
          pnpm_12
          python311
        ];
      };
    };
}
