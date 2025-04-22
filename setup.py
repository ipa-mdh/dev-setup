#!/usr/bin/env python3
from loguru import logger
import argparse
import yaml
from pathlib import Path
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader

target_dir = Path(".dev-setup")
template_dir = Path("dev-setup/template")
templete_docker_dir = template_dir / "docker"
templete_ci_cd_dir = template_dir / "ci-cd"

dev_setup_config_file = Path(".dev-setup.yml")
package_file = Path("package.xml")

DEFAULT_ENVIRONEMNT = "ros.humble"

def parse_arguments():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Setup script with package and environment settings.")
    
    # Add the arguments with default values
    parser.add_argument(
        '--package_name', 
        type=str, 
        default='new_package', 
        help='The name of the package (default: new_package)'
    )
    
    parser.add_argument(
        '--environment', 
        type=str, 
        choices=['ros.noetic', 'ros.humble', 'debian'], 
        default='', 
        help='The environment for the package (default: ros.humble)'
    )
    
    parser.add_argument(
        '--desktop_lite', 
        action='store_true', 
        help='Enable desktop_lite for the devcontainer (default: False)'
    )
    
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help="Automatically answer 'yes' to all prompts"
    )

    # Parse the arguments
    args = parser.parse_args()

    # Return the parsed arguments
    return args

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

def set_package_name(xml_file, new_package_name):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Find the <name> tag and update its text to the new package name
    name_tag = root.find('name')
    if name_tag is not None:
        name_tag.text = new_package_name
    else:
        logger.error("<name> tag not found in the XML file.")
        return
    
    # Write the updated XML back to the file
    tree.write(xml_file, encoding="UTF-8", xml_declaration=True)
    logger.info(f"Package name updated to: {new_package_name}")

def get_dev_setup_template_filename(environment:str):
    if environment:
        filename = f".dev-setup.{environment}.yml.j2"
    else:
        filename = ".dev-setup.yml.j2"
    
    return filename
    
def ask_for_update(variable_name, current_value, new_value, auto_yes):
    """Ask the user whether they want to update the variable. If auto_yes is True, always return the new value."""
    if auto_yes:
        return new_value
    
    while True:
        user_input = input(f"Do you want to update '{variable_name}' with '{new_value}' (current value: {current_value})? (y/n): ").strip().lower()
        if user_input == 'y':
            return new_value
        elif user_input == 'n':
            return current_value
        else:
            print("Invalid input. Please answer with 'y' or 'n'.")

def main():
    args = parse_arguments()
    # Display the parsed values
    logger.info(f"Package Name: {args.package_name}")
    logger.info(f"Environment: {args.environment}")
    logger.info(f"desktop_lite Enabled: {args.desktop_lite}")
    logger.info(f"All yes: {args.yes}")
    
    # exit()
    
    dev_setup_config = {}
    package_name = args.package_name
    
    dev_setup_template_filename = get_dev_setup_template_filename(args.environment)
    
    if dev_setup_config_file.exists():
        logger.info(f"Variables file 'variables_file' found.")
        
        # Load the variables file
        update_config_file = False
        with open(dev_setup_config_file) as f:
            dev_setup_config = yaml.safe_load(f)
            
            if package_name != "new_package":
                # package_name is not the default
                if dev_setup_config['package_name'] != args.package_name:
                    logger.warning(f"The package name in the configuration file differs from the dev-setup argument. {dev_setup_config['package_name']} -> {args.package_name }")
                    dev_setup_config['package_name'] = ask_for_update('package_name',
                                                                      dev_setup_config['package_name'],
                                                                      args.package_name,
                                                                      args.yes)
                    update_config_file = True
            
            if args.environment != '':
                if dev_setup_config['environment'] != args.environment:
                    logger.warning("The environment in the configuration file differs from the dev-setup argument.")
                    dev_setup_config['environment'] = ask_for_update('environment',
                                                                    dev_setup_config['environment'],
                                                                    args.environment,
                                                                    args.yes)
                    update_config_file = True
            
            if dev_setup_config['devcontainer']['feature']['desktop_lite'] != args.desktop_lite:
                logger.warning("The desktop_lite feature in the configuration file differs from the dev-setup argument.")
                dev_setup_config['devcontainer']['feature']['desktop_lite'] = ask_for_update('desktop_lite',
                                                                                             dev_setup_config['devcontainer']['feature']['desktop_lite'],
                                                                                             args.desktop_lite,
                                                                                             args.yes)
                logger.debug(dev_setup_config)
                update_config_file = True
            
        if update_config_file:
            render_template(template_dir / dev_setup_template_filename, dev_setup_config, dev_setup_config_file)
        
    else:
        if args.environment != '':
            dev_setup_config['environment'] = args.environment
        else:
            dev_setup_config['environment'] = DEFAULT_ENVIRONEMNT
        
        dev_setup_config.update({'devcontainer': {'feature': {'desktop_lite': args.desktop_lite}}})
        
        if package_file.exists():
            package_name = get_package_name(package_file)
            dev_setup_config["package_name"] = package_name
        else:
            dev_setup_config["package_name"] = package_name
            logger.warning(f"No package.xml file found. Using '{package_name}' as the package name.")
        render_template(template_dir / dev_setup_template_filename, dev_setup_config, dev_setup_config_file)
    
    with open(dev_setup_config_file) as f:
        dev_setup_config = yaml.safe_load(f)
    
    render_template_folder(templete_docker_dir, dev_setup_config, target_dir / "docker")
    render_template(template_dir / "devcontainer.json.j2", dev_setup_config, Path(".devcontainer/devcontainer.json"))
    render_template_folder(templete_ci_cd_dir, dev_setup_config, target_dir.parent)

if __name__ == "__main__":
    main()