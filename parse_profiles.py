import uuid
from utils.utils import read_api_excel
from collections import defaultdict
data = read_api_excel('API_list.xlsx', sheet_name="API list", return_format="filter")

def is_start(s):
    return s[0] in "0123456789"

api_dict = defaultdict(list)

data_list = []
with open("results/dialogue_profiles_v2.txt", "r") as f:
    d = {}
    for line in f:
        if is_start(line):
            if d:
                print(d)
                assert "Character" in d
                assert "Background" in d
                assert "Purpose" in d
                assert "API" in d
                assert d["API"] in data
                # api_dict[d["API"]].append(d)
                d["uuid"] = uuid.uuid4()
                data_list.append(d)
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
        d["uuid"] = uuid.uuid4()
        data_list.append(d)
        # api_dict[d["API"]].append(d)

with open("results/dialogue_profiles_v2_uuid.txt", "w") as f:
    for idx, d in enumerate(data_list):
        f.write(f"{idx}.\nCharacter: {d['Character']}\nBackground: {d['Background']}\nPurpose: {d['Purpose']}\nAPI: {d['API']}\nParameters: {d['Parameters']}\nuuid: {d['uuid']}\n")
# chunk_size = 5
# part = 0
# for i in range(0, 20, chunk_size):
#     part += 1
#     output_buffer = []
#     for a in api_dict:
#         for api in api_dict[a][i:i+chunk_size]:
#             output_buffer.append(json.dumps(api, ensure_ascii=True))
#     with open(f"results/dialogue_profiles_v1_part{part}.jsonl", "w") as f:
#         f.write("\n".join(output_buffer))

