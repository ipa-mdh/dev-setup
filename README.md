# dev-setup

**dev-setup** is a repository designed to be used as a git submodule inside your **main repository** to streamline local development and CI/CD setups using Docker and VS Code devcontainers. It performs the following tasks:

- **Reads configuration**: It reads the configuration from the `.dev-setup` file and (if available) the `.dev-setup.yml` file in your **main repository** for custom settings.
- **Dockerfile generation**: Creates three Dockerfiles in the generated `.dev-setup/docker/` folder:
  - **base**: This image installs all necessary dependencies but does **not** include any source or binary files from your main repository.
  - **devcontainer**: This image is based on the **base** image and includes all source files, used for an enriched development container experience.
  - **run**: This image is based on the **base** image; it builds your project, removes the source files, and starts the command as defined in your configuration.
- **Devcontainer configuration**: Automatically generates a configuration (`.devcontainer`) that:
  - Uses the **devcontainer** Dockerfile.
  - Installs additional packages as defined in your configuration.
  - Installs recommended VS Code extensions.
- **Security and CI/CD support**:
  - Temporarily imports your `~/.git-credentials` into the Docker image _only during the build process_.
  - Supports passing an access token via environment variables in your GitLab CI/CD pipeline.
- **Default configuration file**: If a `.dev-setup.yml` file does not exist in your **main repository**, the `setup.py` script will create a default `.dev-setup.yml` automatically.

## Usage

### Setting Up dev-setup

1. **Add as a Git Submodule**:  
   In your **main repository**, add **dev-setup** as a submodule. For example:
   ```bash
   git submodule add git@github.com:ipa-mdh/dev-setup.git dev-setup
   ```
   This will clone the **dev-setup** repository into a folder named `dev-setup` in your **main repository**.

2. **Set Up the Configuration**:  
   In your **main repository**, create a `.dev-setup` file if needed. When you run the setup script, it will also check for the presence of a `.dev-setup.yml` file and, if not found, create a default one. This file controls settings such as additional package lists, VS Code extensions to install, and the command to run in the final image.

3. **Generate Dockerfiles and Devcontainer Configuration**:  
   Run the setup script from the **dev-setup** submodule:
   ```bash
   python dev-setup/setup.py
   ```
   This script will:
   - Read the settings in your **main repository**'s `.dev-setup` (and optionally `.dev-setup.yml`) file.
   - Create the necessary three Dockerfiles under `.dev-setup/docker/`.
   - Generate a `.devcontainer` configuration folder with the appropriate settings to launch your development container.
   - Automatically generate a default `.dev-setup.yml` if one does not exist.

### Using the Generated Files

After the setup is complete, follow these steps to build the Docker images and open your repository in a VS Code devcontainer:

1. **Build the Docker Images**:  
   Use the provided build script to build all the necessary Docker images:
   ```bash
   bash ./.dev-setup/docker/build-image.sh
   ```
   This script leverages the generated Dockerfiles (base, devcontainer, and run) to build your container images. Make sure Docker is installed and running on your machine.

2. **Open Your Repository with VS Code in a Devcontainer**:  
   Once the images are built, open your **main repository** folder in VS Code. VS Code will detect the `.devcontainer` folder and prompt you to reopen the folder in a container.  
   - Click on **"Reopen in Container"** when prompted.  
   - If VS Code does not automatically prompt, you can manually open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on macOS) and search for "Remote-Containers: Reopen in Container".

Your repository will now launch inside the configured devcontainer, with all your dependencies, configurations, and VS Code extensions in place, enabling a seamless development experience.

## Example Folder Structure

Below is an example of how your **main repository** structure should look after setting up **dev-setup**:

```
module/                          # Your main repository root
├── dev-setup/                   # The dev-setup git submodule
│   └── (all files of the dev-setup repo)
├── .dev-setup                   # Directory generated by dev-setup/setup.py
│   ├── docker/                  # Contains generated Dockerfiles
│   │   ├── Dockerfile.base     # Base image: dependencies installed, no source files
│   │   ├── Dockerfile.dev      # Devcontainer image: includes all source files
│   │   └── Dockerfile.run      # Run image: builds, strips source files, executes command
│   └── (other artifacts created by the setup)
├── .devcontainer                # Directory generated by dev-setup/setup.py
│   ├── devcontainer.json        # VS Code devcontainer configuration file
│   └── (additional configuration files if necessary)
├── .dev-setup                  # Custom configuration file (if used)
│   └── (your custom dev-setup settings)
├── .dev-setup.yml              # Default configuration file automatically created if it does not exist
├── package.xml                 # Package metadata file (if applicable)
├── src/                         # Your source code directory
├── README.md                    # Your main repository README
└── (other files and directories)
```

## Customizing Settings

- **`.dev-setup` and `.dev-setup.yml`**:  
  You can customize your development environment by editing the `.dev-setup` and `.dev-setup.yml` files in your **main repository**. Use these files to define:
  - The command to run in the final Docker image.
  - Additional packages to install.
  - VS Code extensions to be installed in the devcontainer.
  
- The `setup.py` script ensures that a default `.dev-setup.yml` is created if one is not present, so you always start with a base configuration which you can then modify to suit your project's needs.

## Notes

### Cloning Repositories

- The install script clones repositories **recursively**, ensuring all submodules are included.
- A **shallow clone** downloads only the most recent commits, helping reduce disk space and speed up the cloning process.

If you need the complete commit history later, you can "unshallow" the repository:

```bash
git fetch --unshallow
```

This command fetches the full history from the remote repository, converting your shallow clone into a complete one.

---

With **dev-setup** integrated as a submodule in your **main repository**, you can efficiently manage development dependencies, container setups, and CI/CD integration—all while maintaining a clean separation between source code and container configuration.

Happy coding!