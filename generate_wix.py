"""Generate the wix XML file for the setup generation."""

import argparse
import os
import uuid
import sys
import pickle
from xml.dom import minidom
from xml.etree import ElementTree


def generate_file_list(root_folder):
    """Returns a list of file paths in the given folder.

    :param root_folder the base folder to traverse
    :return list of file paths relative to the root folder
    """
    file_list = []
    for root, _, files in os.walk(root_folder):
        for fname in files:
            file_list.append(
                    os.path.relpath(os.path.join(root, fname), root_folder)
            )
    return file_list


def generate_folder_list(root_folder):
    """Returns a list of folder paths in the given folder.

    :param root_folder the base folder to traverse
    :return list of folder paths relative to the root folder
    """
    folder_list = []
    for root, dirs, _ in os.walk(root_folder):
        for folder in dirs:
            folder_list.append(
                os.path.relpath(os.path.join(root, folder), root_folder)
            )
    return folder_list


def create_data_for_file(path):
    """Creates the entries required to create the file's XML entries.

    :param path the file path for which to create the entries
    :return dictionary containing required information
    """
    return {
        "component_guid": uuid.uuid4(),
        "component_id": "component_{}".format(path.replace("\\", "__")),
        "file_id": "file_{}".format(path.replace("\\", "__")),
        "file_source": path
    }


def create_node(tag, data):
    """Creates a new XML node.

    :param tag the tag of the XML node
    :param data the attributes of the node
    :return newly created XML node
    """
    node = ElementTree.Element(tag)
    for key, value in data.items():
        node.set(key, str(value))
    return node


def create_folder_structure(folder_list):
    """Creates the basic XML direcotry structure.

    :param folder_list the list of folders present
    :return dictionary with folder nodes
    """
    structure = {}

    # Create the basic structure for where to place the actual files
    structure["root"] = create_node(
        "Directory",
        {"Id": "TARGETDIR", "Name": "SourceDir"}
    )
    structure["pfiles"] = create_node(
        "Directory",
        {"Id": "ProgramFilesFolder", "Name": "PFiles"}
    )
    structure["h2ik"] = create_node(
        "Directory",
        {"Id": "H2ik", "Name": "H2ik"}
    )
    structure["jg"] = create_node(
        "Directory",
        {"Id": "INSTALLDIR", "Name": "Joystick Gremlin"}
    )
    structure["root"].append(structure["pfiles"])
    structure["pfiles"].append(structure["h2ik"])
    structure["h2ik"].append(structure["jg"])

    # Component to remove the H2ik folder
    node = create_node(
        "Component",
        {
            "Guid": "cec7a9a7-d686-4355-8d9d-e1d211d3edb8",
            "Id": "H2ikProgramFilesFolder"
        }
    )
    node.append(create_node("RemoveFolder", {"Id": "RemoveH2iKFolder", "On": "uninstall"}))
    structure["h2ik"].append(node)

    # Create the folder structure for the Joystick Gremlin install
    for folder in folder_list:
        dirs = folder.split("\\")
        for i in range(len(dirs)):
            path = "__".join(dirs[:i+1])
            if path not in structure:
                structure[path] = create_node(
                    "Directory",
                    {"Id": path, "Name": dirs[i]}
                )
                if i > 0:
                    parent_path = "__".join(dirs[:i])
                    structure[parent_path].append(structure[path])

        # Link top level folders to the install folder
        if len(dirs) == 1:
            structure["jg"].append(structure[dirs[0]])

    return structure


def add_file_nodes(structure, data):
    """Creates component and file nodes in the appropriate directories.

    :param structure dictionary of directory nodes
    :param data the file node data
    """
    for path, entry in data.items():
        # Create component and file nodes
        c_node = ElementTree.Element("Component")
        c_node.set("Id", entry["component_id"])
        c_node.set("Guid", str(entry["component_guid"]))

        f_node = ElementTree.Element("File")
        f_node.set("Id", entry["file_id"])
        f_node.set("KeyPath", "yes")
        f_node.set("Source", os.path.join("joystick_gremlin", entry["file_source"]))

        c_node.append(f_node)

        # Attach component node to the proper directory node
        parent = os.path.dirname(path).replace("\\", "__")
        if len(parent) == 0:
            parent = "jg"
        structure[parent].append(c_node)


def create_feature(data):
    """Creates the feature node containing all components.

    :param data file structure data
    :return feature node
    """
    node = create_node(
            "Feature",
            {
                "Id": "Complete",
                "Level": 1,
                "Title": "Joystick Gremlin",
                "Description": "The main program",
                "Display": "expand",
                "ConfigurableDirectory": "INSTALLDIR"
            })
    node.append(create_node(
        "ComponentRef", {"Id": "ProgramMenuDir"}
    ))
    node.append(create_node(
        "ComponentRef", {"Id": "H2ikProgramFilesFolder"}
    ))
    for entry in data.values():
        node.append(create_node(
            "ComponentRef",
            {"Id": entry["component_id"]}
        ))
    return node


def create_document():
    """Creates the basic XML document layout.

    :return top level document
    """
    doc = ElementTree.Element("Wix")
    doc.set("xmlns", "http://schemas.microsoft.com/wix/2006/wi")

    prod = create_node(
        "Product",
        {
            "Name": "Joystick Gremlin",
            "Manufacturer": "H2IK",
            #"Id": "a0a7fc85-8651-4b57-b7ee-a7f718857939", # 4.0.0
            "Id": "447529e9-4f78-4baf-b51c-21db602a5f7b", # 4.0.1
            "UpgradeCode": "0464914b-97da-4889-8699-bcde4e767517",
            "Language": "1033",
            "Codepage": "1252",
            "Version": "4.0.1"
        })
    mug = create_node("MajorUpgrade",
        {
            "DowngradeErrorMessage": "Cannot directly downgrade, uninstall current version first."
        }
    )
    pkg = create_node(
        "Package",
        {
            "Id": "*",
            "Keywords": "Installer",
            "Description": "Joystick Gremlin R5 Installer",
            "Manufacturer": "H2IK",
            "InstallerVersion": "100",
            "Languages": "1033",
            "SummaryCodepage": "1252",
            "Compressed": "yes"
        }
    )

    # Package needs to be added before media
    prod.append(pkg)
    prod.append(mug)
    prod.append(create_node(
        "Media",
        {
            "Id": "1",
            "Cabinet": "joystick_gremlin.cab",
            "EmbedCab": "yes"
        }
    ))

    # Add the icon to the software center
    prod.append(create_node(
        "Property",
        {"Id": "ARPPRODUCTICON", "Value": "icon.ico"}
    ))
    # Remvoe the repair option from the installer
    prod.append(create_node(
        "Property",
        {"Id": "ARPNOREPAIR", "Value": "yes", "Secure": "yes"}
    ))

    doc.append(prod)

    return doc


def create_ui_node(parent):
    """Creates the UI definitions.

    :param parent the parent node to which to attach the UI nodes
    """
    ui = create_node("UI", {})
    ui.append(create_node("UIRef", {"Id": "WixUI_InstallDir"}))
    ui.append(create_node("UIRef", {"Id": "WixUI_ErrorProgressText"}))
    ui.append(create_node(
        "Property",
        {"Id": "WIXUI_INSTALLDIR", "Value": "INSTALLDIR"}
    ))

    # Skip the license screen
    n1 = create_node(
        "Publish",
        {
            "Dialog": "WelcomeDlg",
            "Control": "Next",
            "Event": "NewDialog",
            "Value": "InstallDirDlg",
            "Order": "2"
        }
    )
    n1.text = "1"
    n2 = create_node(
        "Publish",
        {
            "Dialog": "InstallDirDlg",
            "Control": "Back",
            "Event": "NewDialog",
            "Value": "WelcomeDlg",
            "Order": 2
        }
    )
    n2.text = "1"
    ui.append(n1)
    ui.append(n2)

    parent.append(ui)


def create_shortcuts(doc, root):
    """Creates program shortcut nodes.

    :param doc the main document
    :param root the root directory node
    """
    # Find the executable node and add shortcut entries
    for node in doc.iter("File"):
        if node.get("Id") == "file_joystick_gremlin.exe":
            node.append(create_node(
                "Shortcut",
                {
                    "Id": "startmenu_joystick_gremlin",
                    "Directory": "ProgramMenuDir",
                    "Name": "Joystick Gremlin",
                    "WorkingDirectory": "INSTALLDIR",
                    "Advertise": "yes",
                    "Icon": "icon.ico"
                }
            ))
            node.append(create_node(
                "Shortcut",
                {
                    "Id": "desktop_joystick_gremlin",
                    "Directory": "DesktopFolder",
                    "Name": "Joystick Gremlin",
                    "WorkingDirectory": "INSTALLDIR",
                    "Advertise": "yes",
                    "Icon": "icon.ico"
                }
            ))

    # Create folder names used for the shortcuts
    n1 = create_node(
        "Directory",
        {"Id": "ProgramMenuFolder", "Name": "Programs"}
    )
    n2 = create_node(
        "Directory",
        {"Id": "ProgramMenuDir", "Name": "Joystick Gremlin"}
    )
    n3 = create_node(
        "Component",
        {"Id": "ProgramMenuDir", "Guid": "e7a50051-e76c-457e-9d43-824ae5ce7ef5"}
    )
    n3.append(create_node(
        "RemoveFolder",
        {"Id": "ProgramMenuDir", "On": "uninstall"}
    ))
    n3.append(create_node(
        "RegistryValue",
        {
            "Root": "HKCU",
            "Key": "Software\H2ik\Joystick Gremlin",
            "Type": "string",
            "Value": "",
            "KeyPath": "yes"
        }
    ))
    n2.append(n3)
    n1.append(n2)
    root.append(n1)

    root.append(create_node(
        "Directory",
        {"Id": "DesktopFolder", "Name": "Desktop"}
    ))

    # Create the used icon
    product = doc.find("Product")
    product.append(create_node(
        "Icon",
        {"Id": "icon.ico", "SourceFile": "joystick_gremlin\gfx\icon.ico"}
    ))


def write_xml(node, fname):
    """Saves the XML document to the given file.

    :param root node of the XML document
    :param fname the file to store the XML document in
    """
    ugly_xml = ElementTree.tostring(node, encoding="unicode")
    dom_xml = minidom.parseString(ugly_xml)
    with open(fname, "w") as out:
        out.write(dom_xml.toprettyxml(indent="    "))


def main():
    # Command line arguments
    parser = argparse.ArgumentParser("Generate WIX component data")
    parser.add_argument("--folder", default="dist/joystick_gremlin", help="Folder to parse")
    args = parser.parse_args()

    # Attempt to load existing file data
    data = {}
    if os.path.exists("wix_data.p"):
        data = pickle.load(open("wix_data.p", "rb"))

    # Create file list and update data for new entries
    file_list = generate_file_list(args.folder)
    for path in file_list:
        if path not in data:
            data[path] = create_data_for_file(path)
    paths_to_delete = []
    for path in data.keys():
        if path not in file_list:
            paths_to_delete.append(path)
    for path in paths_to_delete:
        del data[path]
    pickle.dump(data, open("wix_data.p", "wb"))

    # Create document and file structure
    folder_list = generate_folder_list(args.folder)
    structure = create_folder_structure(folder_list)
    add_file_nodes(structure, data)

    # Assemble the complete XML document
    document = create_document()
    product = document.find("Product")
    product.append(structure["root"])
    product.append(create_feature(data))
    create_shortcuts(document, structure["root"])
    create_ui_node(product)

    # Save the XML document
    write_xml(document, "joystick_gremlin.wxs")

    return 0


if __name__ == "__main__":
    sys.exit(main())