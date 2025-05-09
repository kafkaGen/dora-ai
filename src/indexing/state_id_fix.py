import json
import os

for route in os.listdir("datasets/routes"):
    for step in os.listdir(f"datasets/routes/{route}"):
        node_desc_path = f"datasets/routes/{route}/{step}/node_desc.json"
        with open(node_desc_path, "r") as f:
            node_desc = json.load(f)

        if step == "0":
            node_desc["state_id"] = f"1_1"
        else:
            node_desc["state_id"] = f"{route}_{step}"
        with open(node_desc_path, "w") as f:
            json.dump(node_desc, f, indent=4)


for route in os.listdir("datasets/routes"):
    for step in os.listdir(f"datasets/routes/{route}"):
        action_desc_path = f"datasets/routes/{route}/{step}/action_desc.json"
        node1 = f"datasets/routes/{route}/{step}/node_desc.json"
        node2 = f"datasets/routes/{route}/{int(step)+1}/node_desc.json"

        if not os.path.exists(action_desc_path) or not os.path.exists(node2):
            continue

        with open(action_desc_path, "r") as f:
            action_desc = json.load(f)
        with open(node1, "r") as f:
            node1_desc = json.load(f)
        with open(node2, "r") as f:
            node2_desc = json.load(f)

        for i in range(len(action_desc["state_transitions"])):
            action_desc["state_transitions"][i]["state_id"] = node1_desc["state_id"]
            action_desc["state_transitions"][i]["state_id_2"] = node2_desc["state_id"]

        with open(action_desc_path, "w") as f:
            json.dump(action_desc, f, indent=4)
