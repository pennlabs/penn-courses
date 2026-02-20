import decimal
import json
from collections import OrderedDict, defaultdict
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from degree.models import Degree, Rule
from degree.serializers import RuleSerializer


class DecimalEncoder(json.JSONEncoder):
    """
    JSON encoder that can handle Decimal objects
    """

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)


def recursively_pop(d: dict(), keys: list[str]) -> None:
    """
    Recursively remove keys from a dictionary
    """
    for key in keys:
        if key in d:
            d.pop(key)
    for value in d.values():
        if isinstance(value, dict) or isinstance(value, OrderedDict):
            recursively_pop(value, keys)


def deduplicate_rules(verbose=False):
    rule_to_hash = dict()
    for rule in tqdm(Rule.objects.all(), disable=not verbose, desc="Hashing rules"):
        serialized = RuleSerializer(rule).data  # recursively serializes the rule
        recursively_pop(serialized, keys=["id", "parent"])
        rule_to_hash[rule.id] = hash(
            json.dumps(
                serialized,
                sort_keys=True,
                ensure_ascii=True,
                cls=DecimalEncoder,
            )
        )

    hash_to_rule = defaultdict(list)
    for rule_id, hashed in rule_to_hash.items():
        hash_to_rule[hashed].append(rule_id)

    delete_count = 0
    for rule_ids in tqdm(hash_to_rule.values(), disable=not verbose, desc="Deleting duplicates"):
        if len(rule_ids) > 1:
            Rule.objects.filter(parent_id__in=rule_ids[1:]).update(parent_id=rule_ids[0])
            for degree in Degree.objects.filter(rules__in=rule_ids[1:]):
                degree.rules.add(rule_ids[0])
                degree.rules.remove(*rule_ids[1:])
            deleted, _ = Rule.objects.filter(id__in=rule_ids[1:]).delete()
            delete_count += deleted

    return delete_count


class Command(BaseCommand):
    help = dedent(
        """
        Removes rules that are identical (based on content hash)
        """
    )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        delete_count = deduplicate_rules(verbose=kwargs["verbosity"])
        if kwargs["verbosity"]:
            print(f"Deleted {delete_count} duplicate rules")
