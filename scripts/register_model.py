import argparse
from src.training.model_registry import register_model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--registry", default="models/registry.json")
    args = parser.parse_args()
    print(register_model(args.model, args.metadata, args.registry))


if __name__ == "__main__":
    main()
