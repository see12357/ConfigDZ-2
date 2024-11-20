import os
import sys
import requests
import xml.etree.ElementTree as ET


def get_npm_dependencies(package_name, version, depth, repo_url, dependencies=None, visited=None):
    if dependencies is None:
        dependencies = {}
    if visited is None:
        visited = set()

    if depth == 0:
        return dependencies

    package_key = f"{package_name}:{version}"
    if package_key in visited:
        return dependencies

    visited.add(package_key)
    dependencies[package_key] = []

    response = requests.get(f"{repo_url}/{package_name}/{version}")
    if response.status_code != 200:
        print(f"Не удалось загрузить информацию о пакете: {package_name}@{version}")
        dependencies.pop(package_key, None)  # Удаляем пакет из результата, если запрос неуспешен
        return dependencies

    package_data = response.json()
    package_dependencies = package_data.get("dependencies", {})

    for dep_name, dep_version in package_dependencies.items():
        # Исправляем формат версии
        dep_version = dep_version.lstrip('~^')
        dep_key = f"{dep_name}:{dep_version}"
        dependencies[package_key].append(dep_key)
        get_npm_dependencies(dep_name, dep_version, depth - 1, repo_url, dependencies, visited)

    return dependencies

def sanitize_mermaid_label(label):
    """
    Удаляет неподдерживаемые символы из названия пакета для Mermaid.
    """
    sanitized = label.replace(":", "_").replace(">", "_").replace("<", "_").replace("=", "_").replace(";", "_").replace(" ", "_").replace('@', '_')
    return sanitized.strip("_")

def generate_mermaid_graph(dependencies):
    """
    Генерирует Mermaid-граф с учетом очистки данных.
    """
    mermaid_code = "graph TD;\n"
    for package, deps in dependencies.items():
        sanitized_package = sanitize_mermaid_label(package)
        for dep in deps:
            sanitized_dep = sanitize_mermaid_label(dep)
            mermaid_code += f"    {sanitized_package} --> {sanitized_dep};\n"
    return mermaid_code


def visualize_dependencies(config_file):
    try:
        tree = ET.parse(config_file)
        root = tree.getroot()

        mermaid_path = root.find("mermaidPath").text
        package_name = root.find("packageName").text
        package_version = root.find("packageVersion").text
        depth = int(root.find("maxDepth").text)
        repo_url = root.find("repoUrl").text

        dependencies = get_npm_dependencies(package_name, package_version, depth, repo_url)
        mermaid_code = generate_mermaid_graph(dependencies)

        with open("output.mmd", "w") as f:
            f.write(mermaid_code)

        os.system(f"{mermaid_path} -i output.mmd -o graph.png --width 3860 --height 1440")
        os.remove("output.mmd")

        print("Граф зависимостей успешно сгенерирован и сохранен в 'graph.png'.")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Использование: {sys.argv[0]} <путь_к_конфигурационному_файлу>")
        sys.exit(1)

    config_file = sys.argv[1]
    visualize_dependencies(config_file)
