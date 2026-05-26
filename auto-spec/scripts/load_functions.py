import re
import json

def load_inline():
    with open('scripts/input_data/inline_functions.txt', 'r') as fp:
        return fp.read().splitlines()

def load_function_registry(registry):
    inline = load_inline()
    functions, skipped = [], []
    with open(registry, 'r') as fp:
        lines = fp.read().splitlines()
    curr_fun, curr_fun_data = None, {
        'signatures': []
    }

    for line in lines:
        if line.startswith('-'):
            if 'No Type Checking' in line:
                continue
            if ':' in line:
                fun_alias = line.split(':')[0].removeprefix('- ')
                curr_fun_data['str'] = fun_alias
            for match in re.findall(r"\[[\w,]+\]", line):
                types = match.strip('[]')
                curr_fun_data['signatures'].append(types.lower().split(','))
        else:
            if curr_fun is None:
                pass
            elif curr_fun_data["signatures"] == []:
                skipped.append(curr_fun)
            else:
                functions.append(curr_fun_data)
            curr_fun = line
            curr_fun_data = { 'name': line, 'str': line, 'signatures': [], 'inline': line in inline }

    return functions, skipped

if __name__ == "__main__":
    functions, skipped = load_function_registry('scripts/input_data/functions_raw.txt')
    with open("data/function_signatures.json", "w") as fp:
        json.dump(functions, fp, indent=2)
    with open("data/skipped_functions.json", "w") as fp:
        json.dump(skipped, fp, indent=2)
