from setuptools import setup, find_packages
import os

# Чтение README.md для long_description
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name='tank_battle_game',  # Название вашего проекта
    version='1.0',  # Версия вашего проекта
    author='Ваше имя',  # Ваше имя или имя автора
    author_email='ваш.email@example.com',  # Ваш email
    description='Танковый бой - Многоуровневая игра',  # Краткое описание проекта
    long_description=read_file('README.md'),  # Длинное описание (обычно из README.md)
    long_description_content_type='text/markdown',  # Тип файла описания
    url='https://github.com/ваш_репозиторий',  # Ссылка на репозиторий (если есть)
    packages=find_packages(),  # Автоматически находит все пакеты в проекте
    include_package_data=True,  # Включает дополнительные файлы (например, ресурсы)
    install_requires=[  # Зависимости, которые нужно установить
        'pygame>=2.0.0',
    ],
    classifiers=[  # Классификаторы для PyPI (если вы планируете публиковать проект)
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Минимальная версия Python
    entry_points={  # Точки входа (например, для создания консольных команд)
        'console_scripts': [
            'tank-battle-game = tank_battle_game.main:main_menu',  # Пример команды
        ],
    },
)