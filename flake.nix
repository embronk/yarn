{
  description = "Yarn — a stack-based programming language shaped like a crochet pattern";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems f;
    in
    {
      packages = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = pkgs.stdenvNoCC.mkDerivation {
            pname = "yarn-lang";
            version = "0.1.0";
            src = ./.;

            dontBuild = true;
            nativeBuildInputs = [ pkgs.makeWrapper ];

            installPhase = ''
              mkdir -p $out/share/yarn-lang $out/bin
              install -Dm755 yarn_interpreter.py $out/share/yarn-lang/yarn_interpreter.py
              cp -r examples $out/share/yarn-lang/examples

              makeWrapper ${pkgs.python3}/bin/python3 $out/bin/yarn \
                --add-flags "$out/share/yarn-lang/yarn_interpreter.py"
            '';

            meta = with pkgs.lib; {
              description = "A crochet-pattern-inspired esoteric programming language";
              license = licenses.mit;
              mainProgram = "yarn";
            };
          };
        });

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/yarn";
        };
      });

      devShells = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = pkgs.mkShell {
            packages = [ pkgs.python3 ];
          };
        });
    };
}
