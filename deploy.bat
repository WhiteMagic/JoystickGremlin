@echo "Starting to build Gremlin ..."
cd /d %0\..

@echo "Installing dependencies with Poetry ..."
poetry install

@echo "Building executable ..."
poetry run pyinstaller -y --clean joystick_gremlin.spec

@echo "Compress the build ..."
cd dist
powershell -Command "Compress-Archive -Path * -DestinationPath joystick_gremlin_build.zip"

cd ..

@pause
