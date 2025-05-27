{
  description = "Multi-Python environment using uv2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    uv2nix.url = "github:pyproject-nix/uv2nix";
  };

  outputs = { self, nixpkgs, flake-utils, uv2nix, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        pythonVersions = {
          python39 = pkgs.python39;
          python310 = pkgs.python310;
          python311 = pkgs.python311;
          python312 = pkgs.python312;
          python313 = pkgs.python313;
          python314 = pkgs.python314;
        };

        devShells = builtins.mapAttrs (name: python:
          let
            uvWorkspace = uv2nix.lib.loadWorkspace {
              inherit pkgs;
              src = ./.;
            };
            pythonSet = uvWorkspace.mkPythonSet {
              inherit python;
            };
          in
            pythonSet.mkDevShell { }
        ) pythonVersions;

        # Set default devShell (e.g., Python 3.11)
        defaultDevShell = let
          uvWorkspace = uv2nix.lib.loadWorkspace {
            inherit pkgs;
            src = ./.;
          };
          pythonSet = uvWorkspace.mkPythonSet {
            python = pkgs.python311;
          };
        in pythonSet.mkDevShell { };
      in {
        devShells = devShells // { default = defaultDevShell; };
      });
}
