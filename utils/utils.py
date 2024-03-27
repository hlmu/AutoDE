import pandas as pd
import re
from collections import defaultdict

SPECIAL_TYPES = {
    "estimateTime": "boolean",
    "estimateDistance": "boolean",
}

ENUM_MAP_ENG = {
    "deviceType": ["mobile phone", "tablet", "TV", "speaker", "watch"],
    "ticketType": ["plane", "train", "boat", "bus"]
}

OPENAI_INFO = {
    "gpt-35-turbo-16k": {
        "model": "gpt-3.5-turbo-16k-0613",
        "api_key": "",
        "api_key_list": [
            ""
        ]
    },
    "gpt-35-turbo-azure": {
        "engine": "35turbo",
        "api_base": "https://",
        "api_version": "2023-07-01-preview",
        "api_type": "azure",
        "api_key": "",
    }
}

CLAUDE_PROXY_INFO = {
    "claude_2": {
        "model": "claude-2",
    },
    "claude_1": {
        "model": "claude-1",
    },
    "claude_instant_1": {
        "model": "claude-instant-1",
    },
    "claude_instant_1_2": {
        "model": "claude-instant-1.2",
    },
}

CLAUDE_PROXY_KEY = ""

def trim_nan(s):
    return "" if s == "nan" else s

def read_api_excel(filename: str, sheet_name: str, return_format: str):
    df = pd.read_excel(filename, sheet_name=sheet_name) 

    df['domain'] = df['domain'].astype(str)
    df['subdomain'] = df['subdomain'].astype(str)
    df['function'] = df['function'].astype(str)
    df['api'] = df['api'].astype(str)
    df['description'] = df['description'].astype(str)
    df['parameters'] = df['parameters'].astype(str)

    if return_format == "openai_eng":
        data = []
        for index, row in df.iterrows():
            if trim_nan(row["api"]).strip() == "":
                continue
            required = []
            parameters_any = []
            if row['parameters'] == 'nan':
                parameters_dict = {}
            else:
                parameters = row['parameters'].strip().split('\n')
                parameters = [param.strip() for param in parameters]
                parameters_dict = {}
                for param in parameters:
                    k_v = param.split(": ")
                    assert len(k_v) == 2, k_v
                    if ("" in k_v[1]):
                        k_v[1] = k_v[1].replace("(required slot)", "").strip()
                        required.append(k_v[0])
                    if ("(optional slot)" in k_v[1]):
                        k_v[1] = k_v[1].replace("(optional slot)", "").strip()
                        parameters_any.append(k_v[0])
                    parameter_item = {
                        "type": SPECIAL_TYPES.get(k_v[0], "string"),
                        "description": k_v[1],
                    }
                    if k_v[0] in ENUM_MAP_ENG:
                        parameter_item["enum"] = ENUM_MAP_ENG[k_v[0]]
                    parameters_dict[k_v[0]] = parameter_item
            description = trim_nan(row["description"])
            if len(parameters_any) > 0:
                description = description.rstrip(".") + f". The call must contain at least one of the following parameters: {', '.join(parameters_any)}"
            name = trim_nan(row["api"])
            # name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower().replace('.', '')
            function = {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters_dict,
                    "required": required,
                },
            }
            data.append(function)
    elif return_format == "local":
        data = []
        for index, row in df.iterrows():
            if row['parameters'] == 'nan':
                parameters_dict = {}
            else:
                parameters = row['parameters'].strip().split('\n')
                parameters = [param.strip() for param in parameters]
                parameters_dict = {}
                for param in parameters:
                    k_v = param.split(": ")
                    assert len(k_v) == 2, k_v
                    parameters_dict[k_v[0]] = k_v[1]
            d = {
                "domain": trim_nan(row["domain"]),
                "subdomain": trim_nan(row["subdomain"]),
                "function": trim_nan(row["function"]),
                "api": trim_nan(row["api"]),
                "description": trim_nan(row["description"]),
                "parameters": parameters_dict
            }
            data.append(d)
    elif return_format == "filter":
        data = {}
        for index, row in df.iterrows():
            if trim_nan(row["api"]).strip() == "":
                continue
            required = []
            parameters_any = []
            parameters_all = []
            if row['parameters'] != 'nan':
                parameters = row['parameters'].strip().split('\n')
                parameters = [param.strip() for param in parameters]
                parameters_dict = {}
                for param in parameters:
                    k_v = param.split(": ")
                    assert len(k_v) == 2, k_v
                    if ("（必选槽位）" in k_v[1]):
                        required.append(k_v[0])
                    if ("（任选槽位）" in k_v[1]):
                        parameters_any.append(k_v[0])
                    parameters_all.append(k_v[0])
            name = trim_nan(row["api"])
            data[name] = {
                "required": required,
                "parameters_any": parameters_any,
                "parameters_all": parameters_all
            }

    return data


def parse_profile(profile_path):
    data = read_api_excel('API_list.xlsx', sheet_name="API list", return_format="filter")

    def is_start(s):
        return s[0] in "0123456789"

    profile_data = []
    with open(profile_path, "r") as f:
        d = {}
        for line in f:
            if is_start(line):
                if d:
                    # print(d)
                    assert "Character" in d
                    assert "Background" in d
                    assert "Purpose" in d
                    assert "API" in d
                    assert d["API"] in data
                    assert "Parameters" in d
                    profile_data.append(d)
                    d = {}
            else:
                k, v = line.split(": ", maxsplit=1)
                d[k] = v.strip()

        if d:
            assert "Character" in d
            assert "Background" in d
            assert "Purpose" in d
            assert "API" in d
            assert d["API"] in data
            profile_data.append(d)
    return profile_data


if __name__ == "__main__":
    read_api_excel("API_list.xlsx", sheet_name="API list", return_format="filter")
    parse_profile("results/dialogue_profiles_v2.txt")