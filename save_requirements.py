import pkg_resources


def save_installed_packages(filename):
    installed_packages = sorted(
        pkg_resources.working_set,
        key=lambda package: package.project_name.lower()
    )
    with open(filename, 'w') as file:
        for package in installed_packages:
            package_line = f"{package.project_name}=={package.version}\n"
            file.write(package_line)

# Example usage
save_installed_packages('requirements.txt')
