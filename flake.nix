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

    nixosModules.default = {
      config,
      lib,
      pkgs,
      ...
    }: let
      cfg = config.services.media-bot;
      package = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
      env =
        lib.mapAttrs' (
          name: value:
            lib.nameValuePair (lib.toUpper name) (toString value)
        )
        cfg.settings;
    in {
      options.services.media-bot = {
        enable = lib.mkEnableOption "Media Bot";

        package = lib.mkOption {
          type = lib.types.package;
          default = package;
          defaultText = "self.packages.\${pkgs.stdenv.hostPlatform.system}.default";
          description = "The media-bot package to run.";
        };

        user = lib.mkOption {
          type = lib.types.str;
          default = "media-bot";
          description = "User account under which media-bot runs.";
        };

        group = lib.mkOption {
          type = lib.types.str;
          default = "media-bot";
          description = "Group account under which media-bot runs.";
        };

        environmentFile = lib.mkOption {
          type = lib.types.nullOr lib.types.path;
          default = null;
          example = "/run/secrets/media-bot.env";
          description = "Optional EnvironmentFile containing secrets such as TELEGRAM_BOT_TOKEN and OPENAI_API_KEY.";
        };

        settings = lib.mkOption {
          type = lib.types.attrsOf (
            lib.types.oneOf [
              lib.types.str
              lib.types.path
              lib.types.int
              lib.types.bool
            ]
          );
          default = {};
          example = {
            QBITTORRENT_HOST = "http://127.0.0.1:8080";
            DOWNLOAD_DIR = "/downloads";
            MOVIES_DIR = "/media/movies";
            SERIES_DIR = "/media/series";
            DATABASE_PATH = "/var/lib/media-bot/media_bot.sqlite3";
          };
          description = "Environment variables passed to media-bot.";
        };
      };

      config = lib.mkIf cfg.enable {
        users.groups.${cfg.group} = {};
        users.users.${cfg.user} = {
          isSystemUser = true;
          group = cfg.group;
          home = "/var/lib/media-bot";
          createHome = true;
        };

        systemd.services.media-bot = {
          description = "Media Bot";
          wantedBy = ["multi-user.target"];
          after = ["network-online.target"];
          wants = ["network-online.target"];

          environment =
            {
              DATABASE_PATH = "/var/lib/media-bot/media_bot.sqlite3";
            }
            // env;

          serviceConfig =
            {
              ExecStart = "${lib.getExe cfg.package}";
              User = cfg.user;
              Group = cfg.group;
              StateDirectory = "media-bot";
              WorkingDirectory = "/var/lib/media-bot";
              Restart = "on-failure";
              RestartSec = "10s";
            }
            // lib.optionalAttrs (cfg.environmentFile != null) {
              EnvironmentFile = cfg.environmentFile;
            };
        };
      };
    };

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
