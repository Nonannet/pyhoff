import importlib
import inspect
import fnmatch
from io import TextIOWrapper


def write_classes(f: TextIOWrapper, patterns: list[str], module_name: str, title: str, description: str = '', exclude: list[str] = []) -> None:

    module = importlib.import_module(module_name)

    classes = [
        name for name, obj in inspect.getmembers(module, inspect.isclass)
        if (obj.__module__ == module_name and
            any(fnmatch.fnmatch(name, pat) for pat in patterns if pat not in exclude) and
            obj.__doc__ and '(Automatic generated stub)' not in obj.__doc__)
    ]

    """Write the classes to the file."""
    f.write(f'## {title}\n\n')
    if description:
        f.write(f'{description}\n\n')

    for cls in classes:
        f.write('```{eval-rst}\n')
        f.write(f'.. autoclass:: {module_name}.{cls}\n')
        f.write('   :members:\n')
        f.write('   :undoc-members:\n')
        f.write('   :show-inheritance:\n')
        f.write('   :inherited-members:\n')
        if title != 'Base classes':
            f.write('   :exclude-members: select\n')
        f.write('```\n\n')


with open('docs/source/modules.md', 'w') as f:
    f.write('# Classes\n\n')
    write_classes(f, ['BK*', 'WAGO_750_352'], 'pyhoff.devices', title='Bus coupler',
                  description='These classes are bus couplers and are used to connect the IO bus terminals to a Ethernet interface.')
    write_classes(f, ['KL*'], 'pyhoff.devices', title='Beckhoff bus terminals')
    write_classes(f, ['WAGO*'], 'pyhoff.devices', title='WAGO bus terminals', exclude=['WAGO_750_352'])
    write_classes(f, ['*'], 'pyhoff', title='Base classes',
                  description='These classes are base classes for devices and are typically not used directly.')
    write_classes(f, ['*'], 'pyhoff.modbus', title='Modbus',
                  description='This modbus implementation is used internally.')
