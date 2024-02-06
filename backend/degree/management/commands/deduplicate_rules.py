from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction
from degree.models import Rule 
from degree.serializers import RuleSerializer
import json
from collections import defaultdict

class Command(BaseCommand):
    help = dedent(
        """ 
        Removes rules that are identical (based on content hash except for rule ids)
        """
    )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # get toposort of rules
        rules = list(Rule.objects.filter(parent=None).order_by('id'))
        
        # serialize rules to fixed format
        rules = {
            rule.id: hash(json.dumps(
                RuleSerializer(rule).data, 
                sort_keys=True, 
                ensure_ascii=True
            ))
            for rule in rules
        }

        # invert rules
        inverted_rules = defaultdict(list)
        for rule, hash in rules.items():
            inverted_rules[hash].append(rule)
        
        # fold the rules
        for hash, rule_ids in inverted_rules.items():
            if len(rule_ids) > 1:
                print(f"Removing rules {rule_ids[1:]}")
                Rule.objects.filter(id__in=rule_ids[1:]).values_list("parent_id", flat=True).update(parent_id=rule_ids[0]
        



