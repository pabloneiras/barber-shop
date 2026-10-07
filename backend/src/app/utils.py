def normalize_phone(phone: str):
    # 1. Remove all whitespace first
    phone = "".join(phone.split(" "))
    # Remove all hyphens
    phone = phone.replace("-", "")
    # 2. If it includes the "+34" prefix, remove it
    if phone.startswith("+34"):
        phone = phone.replace("+34", "")
    return phone

