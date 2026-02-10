from django import template
register = template.Library()

@register.filter
def dict_get(dict_data, key):
    return dict_data.get(key)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def split_and_capitalize(value):
    try:
        part1, part2 = value.split('_', 1)
        return f"{part1.upper()}  {part2.upper()}"
    except ValueError:
        return value.upper()