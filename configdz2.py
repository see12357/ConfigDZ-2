import os
import sys
import requests
import xml.etree.ElementTree as ET

def get_npm_dependencies(package_name, version, depth, repo_url, dependencies=None, visited=None):
    # Инициализация структуры данных
    if dependencies is None:
        dependencies = {}
    if visited is None:
        visited = set()

    # Прекращаем обработку, если достигнута максимальная глубина
    if depth == 0:
        return dependencies

    package_key = f"{package_name}:{version}"
    if package_key in visited:
        return dependencies

    visited.add(package_key)
    dependencies[package_key] = []

    # Запрашиваем информацию о пакете из NPM-репозитория
    response = requests.get(f"{repo_url}/{package_name}/{version}")
    if response.status_code != 200:
        print(f"Не удалось загрузить информацию о пакете: {package_name}@{version}")
        return dependencies

    package_data = response.json()
    package_dependencies = package_data.get("dependencies", {})

    # Рекурсивно обрабатываем зависимости
    for dep_name, dep_version in package_dependencies.items():
        dep_key = f"{dep_name}:{dep_version}"
        dependencies[package_key].append(dep_key)
        get_npm_dependencies(dep_name, dep_version, depth - 1, repo_url, dependencies, visited)

    return dependencies

def generate_mermaid_graph(dependencies):
    # Формирование Mermaid-кода
    mermaid_code = "graph TD;\n"
    for package, deps in dependencies.items():
        for dep in deps:
            mermaid_code += f"{package} --> {dep}\n"
    return mermaid_code

def visualize_dependencies(config_file):
    # Чтение конфигурационного файла
    tree = ET.parse(config_file)
    root = tree.getroot()

    # Извлечение параметров из XML
    mermaid_path = root.find("mermaidPath").text
    package_name = root.find("packageName").text
    package_version = root.find("packageVersion").text
    depth = int(root.find("maxDepth").text)
    repo_url = root.find("repoUrl").text

    # Получение зависимостей
    dependencies = get_npm_dependencies(package_name, package_version, depth, repo_url)

    # Генерация Mermaid-кода
    mermaid_code = generate_mermaid_graph(dependencies)

    # Запись временного файла с Mermaid-кодом
    with open("output", "w") as f:
        f.write(mermaid_code)

    # Визуализация графа и вывод результата
    os.system(f"{mermaid_path} output -o graph.png")
    os.remove("output")

    print("Граф зависимостей успешно сгенерирован и сохранен в 'graph.png'.")

if __name__ == "__main__":
    # Проверяем наличие аргумента с конфигурационным файлом
    if len(sys.argv) != 2:
        print(f"Использование: {sys.argv[0]} <путь_к_конфигурационному_файлу>")
        sys.exit(1)

    config_file = sys.argv[1]
    visualize_dependencies(config_file)
