{
  description = "Multi-Python environment using uv2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    uv2nix.url = "github:pyproject-nix/uv2nix";
    uv2nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, uv2nix, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { 
          inherit system;
          config = {
            allowUnfree = true;
          };
        };

        # Python versions matching your .envrc
        pythonVersions = {
          python311 = pkgs.python311;
          python312 = pkgs.python312;
          python313 = pkgs.python313;
        };

        # Common tools needed for development
        commonTools = with pkgs; [
          # uv for Python package management
          uv
          
          # Build tools that might be needed for Python packages
          gcc
          pkg-config
          
          # Git for version control
          git
          
          # Make for your build system
          gnumake
          
          # Common libraries that Python packages might need
          zlib
          openssl
          libffi
          
          # Optional but useful tools
          curl
          wget
          tree
          jq
        ];

        # Create development shells for each Python version
        devShells = builtins.mapAttrs (name: python:
          pkgs.mkShell {
            buildInputs = [ python ] ++ commonTools;
            
            shellHook = ''
              echo "Entering ${name} development environment"
              echo "Python: $(${python}/bin/python --version)"
              echo "uv: $(uv --version)"
              
              # Ensure UV doesn't try to manage Python installations
              export UV_PYTHON_DOWNLOADS=never
              export UV_NO_MANAGED_ENV=1
              
              # Add scripts directory to PATH
              export PATH="$PWD/scripts:$PATH"
              
              # Set up environment for this Python version
              export PYTHON_VERSION="${builtins.replaceStrings ["python"] [""] name}"
            '';
          }
        ) pythonVersions;

        # Default development shell (Python 3.11 as per your setup)
        defaultDevShell = pkgs.mkShell {
          buildInputs = [ pythonVersions.python311 ] ++ commonTools;
          
          shellHook = ''
            echo "Entering default Python development environment"
            echo "Python: $(${pythonVersions.python311}/bin/python --version)"
            echo "uv: $(uv --version)"
            
            # Environment variables to match your .envrc
            export PYTHON_VERSIONS="3.11 3.12 3.13"
            export UV_PYTHON_DOWNLOADS=never
            export UV_NO_MANAGED_ENV=1
            
            # Add scripts directory to PATH
            export PATH="$PWD/scripts:$PATH"
            
            # Make the make.py script executable if it isn't already
            if [ -f scripts/make.py ]; then
              chmod +x scripts/make.py
            fi
            
            echo ""
            echo "Available commands:"
            echo "  make.py setup    - Setup all virtual environments"
            echo "  make.py help     - Show all available tasks"
            echo "  make.py clean    - Clean build artifacts"
            echo ""
            echo "You can also use 'uv' commands directly."
          '';
        };

        # Optional: Create a shell for each specific Python version
        namedShells = builtins.mapAttrs (name: python:
          pkgs.mkShell {
            buildInputs = [ python ] ++ commonTools;
            shellHook = ''
              echo "Entering ${name} specific environment"
              export UV_PYTHON_DOWNLOADS=never
              export UV_NO_MANAGED_ENV=1
              export PATH="$PWD/scripts:$PATH"
            '';
          }
        ) pythonVersions;

      in {
        devShells = devShells // namedShells // { 
          default = defaultDevShell; 
        };
        
        # Optional: Add packages that can be built
        packages = {
          default = pkgs.writeShellScriptBin "dev-env" ''
            echo "Python development environment ready!"
            echo "Use 'nix develop' to enter the development shell."
          '';
        };
        
        # Optional: Add apps for easy access
        apps = {
          setup = {
            type = "app";
            program = "${pkgs.writeShellScript "setup" ''
              cd $PWD
              ${pkgs.python311}/bin/python scripts/make.py setup
            ''}";
          };
        };
      });
}