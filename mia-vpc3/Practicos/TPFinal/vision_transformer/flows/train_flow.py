from prefect import flow

@flow
def execute_flow() -> None:
    raise NotImplementedError("This flow is not implemented yet. Please implement the evaluation logic.")


if __name__ == "__main__":
    execute_flow()
