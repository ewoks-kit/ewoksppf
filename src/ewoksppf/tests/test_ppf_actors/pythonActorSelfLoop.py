def run(index=0, limit=10, **kwargs):
    index += 1
    return {"index": index, "has_data": index < limit}
