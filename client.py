import requests, json
from typing import List, Optional, Union
import yaml


# Load the configurations by reading the config yaml file
def read_config(file_path: str) -> dict:
    with open(file_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def send_request(host, port, endpoint_name, request_data: dict):
    url = f"http://{host}:{port}/{endpoint_name}"
    request_data = json.dumps(request_data)
    response = requests.post(url, data=request_data, stream=True)
    return response


def generate_word(
    connection_params: dict,
    generation_params: dict,
    conv: Optional[List] = None,
    input_text: Optional[str] = None,
):
    if input_text is not None and conv is not None:
        conv.append(dict(role="user", content=input_text))
        the_model_input = conv
    elif input_text is not None:
        the_model_input = input_text
    else:
        raise ValueError("Conversation and input strings both are None")

    request_data = dict(
        input_messages=the_model_input,
        generation_params=generation_params,
    )

    generated_text = ""
    response = send_request(request_data=request_data, **connection_params)

    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        chunk = json.loads(chunk)
        new_text = chunk["new_word"]
        yield new_text
        generated_text += new_text

    if conv is not None:
        conv.append(dict(role="assistant", content=generated_text))


def main(configs):

    generation_params = configs["generation_params"]
    connection_params = configs["connection_params"]

    while True:
        try:
            input_text = input("INPUT: ")
            if input_text == "":
                print("Invalid input, input cannot be empty.")
                continue

            generation_params = {
                "max_new_tokens": 4096,
                "handle_long_generation": "hole",
                "return_full_text": False,  # Does not have any effect.
            }
            for word in generate_word(
                input_text=input_text,
                connection_params=connection_params,
                generation_params=generation_params,
            ):
                print(word, end="", flush=True)
            print()
        except KeyboardInterrupt:
            exit()


if __name__ == "__main__":
    config_file_path = "./client_config.yaml"

    configs = read_config(config_file_path)
    main(configs)
