#!/usr/bin/env python3
import yaml
from pathlib import Path
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader

target_dir = Path(".dev-setup")
template_dir = Path("dev-setup/template")
templete_docker_dir = template_dir / "docker"

variables_file = Path(".dev-setup.yml")
package_file = Path("package.xml")

def render_template(file: Path, variables: dict, targtet: Path):
    # Load the Jinja2 template   
    env = Environment(loader=FileSystemLoader(file.parent))
    template = env.get_template(file.name)

    # Render the Dockerfile
    output = template.render(variables)

    # Create the target directory if it doesn't exist
    if not targtet.parent.exists():
        targtet.parent.mkdir(parents=True)
        
    # Write the output to a file
    with open(targtet, "w") as f:
        f.write(output)

def render_template_folder(template_dir, variables, output_dir):
    # get template files
    template_files = list(template_dir.glob("*.j2"))

    for file in template_files:
        render_template(file, variables, output_dir / file.with_suffix("").name)

def get_package_name(package_xml_path: Path):
    """Extracts the package name from a package.xml file."""
    if not package_xml_path.exists():
        raise FileNotFoundError(f"The file {package_xml_path} does not exist.")

    tree = ET.parse(package_xml_path)
    root = tree.getroot()

    # The <name> tag is expected to be a direct child of the root element.
    name_elem = root.find('name')
    if name_elem is None:
        raise ValueError("No <name> element found in the package.xml file.")

    return name_elem.text.strip()
    

def main():
    # Load the variables file
    with open(variables_file) as f:
        variables = yaml.safe_load(f)
        
    if package_file.exists():
        package_name = get_package_name(package_file)
        variables["package_name"] = package_name
    else:
        variables["package_name"] = "my_package"
    
    render_template_folder(templete_docker_dir, variables, target_dir / "docker")
    render_template(template_dir / "devcontainer.json.j2", variables, Path(".devcontainer/devcontainer.json"))
    
    dev_setup_config_file = Path(".dev-setup.yml")
    if not dev_setup_config_file.exists():
        render_template(template_dir / ".dev-setup.yml.j2", variables, dev_setup_config_file)

if __name__ == "__main__":
    main()