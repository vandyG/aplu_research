let
  # Stable and unstable nixpkgs
  stablePkgs = import <nixpkgs> { };
  unstablePkgs = import (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz";
  }) { };

  inherit (stablePkgs) lib;

  libraryPath = with stablePkgs; lib.makeLibraryPath [ stdenv.cc.cc.lib ];

  pyproject-nix =
    import
      (builtins.fetchGit {
        url = "https://github.com/pyproject-nix/pyproject.nix.git";
      })
      {
        inherit lib;
      };

  uv2nix =
    import
      (builtins.fetchGit {
        url = "https://github.com/pyproject-nix/uv2nix.git";
      })
      {
        inherit pyproject-nix lib;
      };

  pyproject-build-systems =
    import
      (builtins.fetchGit {
        url = "https://github.com/pyproject-nix/build-system-pkgs.git";
      })
      {
        inherit pyproject-nix uv2nix lib;
      };

in
stablePkgs.mkShell {

  packages = with stablePkgs; [
    (python311.withPackages (python-pkgs: with python-pkgs; [
      python
      numpy_2
      pip
      jupyter
      notebook
      ipykernel
    ]))
    (python312.withPackages (python-pkgs: with python-pkgs; [
      python
      numpy_2
      pip
      jupyter
      notebook
      ipykernel
    ]))
    (unstablePkgs.python313.withPackages (python-pkgs: with python-pkgs; [
      python
      numpy_2
      pip
      jupyter
      notebook
      ipykernel
    ]))
    unstablePkgs.uv
    unstablePkgs.ruff
    nil
    nixfmt-rfc-style
  ];


  shellHook = ''
    export TMPDIR=/tmp
    export LD_LIBRARY_PATH=${libraryPath}:$LD_LIBRARY_PATHx
    export RUFF_PATH=$(which ruff)
    export PYTHON311=$(which python3.11)
    export PYTHON312=$(which python3.12)
    export PYTHON313=$(which python3.13)
    echo "Shell with multiple Python versions, uv (from unstable), and uv2nix tooling."
  '';
}