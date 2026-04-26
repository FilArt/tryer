{
  description = "Media Bot";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
    ...
  }: let
    supportedSystems = [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ];

    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
  in {
    packages = forAllSystems (system: let
      pkgs = import nixpkgs {inherit system;};
      python = pkgs.python312;
      pythonPackages = python.pkgs;
      pythonTelegramBot = pythonPackages.python-telegram-bot.overridePythonAttrs (_: {
        doCheck = false;
      });
    in {
      default = pythonPackages.buildPythonApplication {
        pname = "media-bot";
        version = "0.1.0";
        pyproject = true;

        src = pkgs.lib.cleanSourceWith {
          src = ./.;
          filter = path: type: let
            baseName = baseNameOf path;
          in
            !(pkgs.lib.elem baseName [
              ".devenv"
              ".direnv"
              ".env"
              ".git"
              "media_bot.sqlite3"
            ]);
        };

        build-system = [pythonPackages.setuptools];

        dependencies = with pythonPackages; [
          openai
          python-dotenv
          pythonTelegramBot
          qbittorrent-api
        ];

        pythonImportsCheck = ["media_bot"];

        meta = {
          mainProgram = "media-bot";
        };
      };
    });

    apps = forAllSystems (system: {
      default = {
        type = "app";
        program = "${nixpkgs.lib.getExe self.packages.${system}.default}";
        meta.description = "Run Media Bot";
      };
    });

    devShells = forAllSystems (system: let
      pkgs = import nixpkgs {inherit system;};
    in {
      default = pkgs.mkShell {
        packages = [
          pkgs.python312
          pkgs.uv
        ];
      };
    });
  };
}
