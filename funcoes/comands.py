def comand_is_valid(comand: str) -> bool:
    """Valida se o comando é reconhecido"""
    list_of_comands: list = ["#back", "#help", "#clear_history", "#add", "#add_rota", "#sair"]
    if not comand or comand[0] != "#":
        return False
    elif comand not in list_of_comands:
        return False
    else:
        return True