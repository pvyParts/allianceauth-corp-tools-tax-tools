import logging
from datetime import timedelta
from typing import List

from allianceauth.eveonline.models import EveCharacter
from corptools.models import EveItemType, EveLocation
from corptools.providers import esi
from corptools.schema import CharacterWalletEvent
from corptools.task_helpers.corp_helpers import get_corp_token
from django.conf import settings
from django.utils import timezone
from ninja import NinjaAPI
from ninja.responses import codes_4xx
from ninja.security import django_auth

from . import models

logger = logging.getLogger(__name__)

api = NinjaAPI(title="Tax Tools API", version="0.0.1",
               urls_namespace='taxtools:api', auth=django_auth, csrf=True,)
# openapi_url=settings.DEBUG and "/openapi.json" or "")


@api.get(
    "char/tax/list",
    tags=["Character Taxes"],
    response={200: List[CharacterWalletEvent]},
)
def get_char_tax_data(request, days=90, conf_id=1):
    if not request.user.is_superuser:
        return []
    start = timezone.now() - timedelta(days=days)

    t = models.CharacterPayoutTaxConfiguration.objects.get(id=conf_id)

    output = []
    for w in t.get_payment_data(start_date=start):
        output.append(
            {
                "character": w.character.character,
                "id": w.entry_id,
                "date": w.date,
                "first_party": {
                    "id": w.first_party_id,
                    "name": w.first_party_name.name,
                    "cat": w.first_party_name.category,
                },
                "second_party":  {
                    "id": w.second_party_id,
                    "name": w.second_party_name.name,
                    "cat": w.second_party_name.category,
                },
                "ref_type": w.ref_type,
                "amount": w.amount,
                "balance": w.balance,
                "reason": w.reason,
            })

    return output


@api.get(
    "char/tax/aggregates",
    tags=["Character Taxes"],
)
def get_char_tax_aggregates(request, days=90, conf_id=1):
    if not request.user.is_superuser:
        return []
    start = timezone.now() - timedelta(days=days)
    t = models.CharacterPayoutTaxConfiguration.objects.get(id=conf_id)
    tx = t.get_character_aggregates(start_date=start)

    return tx


@api.get(
    "char/tax/aggregates/corp",
    tags=["Character Taxes"],
)
def get_char_tax_aggregates_corp(request, days=90, conf_id=1):
    if not request.user.is_superuser:
        return []
    start = timezone.now() - timedelta(days=days)
    t = models.CharacterPayoutTaxConfiguration.objects.get(id=conf_id)
    tx = t.get_character_aggregates_corp_level(start_date=start)
    return tx


@api.get(
    "char/tax/aggregates/groups",
    tags=["Character Taxes"],
)
def get_char_tax_aggregate_groups(request, days=90, conf_id=1):
    if not request.user.is_superuser:
        return []
    start = timezone.now() - timedelta(days=days)
    t = models.CharacterPayoutTaxConfiguration.objects.get(id=conf_id)
    tx = t.get_aggregates(start_date=start)

    output = {}
    for w in tx:
        if w['corp'] not in output:
            output[w['corp']] = {
                "characters": [],
                "sum": 0,
                "tax": 0,
                "cnt": 0,
            }
        output[w['corp']]["characters"].append(w['char'])
        output[w['corp']]["sum"] += w['sum_amount']
        output[w['corp']]["tax"] += w['tax_amount']
        output[w['corp']]["cnt"] += w['cnt_amount']

    return output


@api.get(
    "corp/{corp_id}/tax/history",
    tags=["Corporation Helpers"],
)
def get_tax_history(request, corp_id: int):
    if not request.user.is_superuser:
        return []
    return models.CorpTaxHistory.get_corp_tax_list(corp_id)


@api.get(
    "corp/{corp_id}/tax/history/find",
    tags=["Corporation Helpers"],
)
def find_tax_history(request, corp_id: int):
    if not request.user.is_superuser:
        return []
    return models.CorpTaxHistory.find_corp_tax_changes(corp_id)


@api.get(
    "corp/{corp_id}/tax/history/sync",
    tags=["Corporation Helpers"],
)
def sync_tax_history(request, corp_id: int):
    if not request.user.is_superuser:
        return []
    return models.CorpTaxHistory.sync_corp_tax_changes(corp_id)


@api.get(
    "corp/tax/history/sync/all",
    tags=["Corporation Helpers"],
)
def sync_all_tax_histories(request):
    if not request.user.is_superuser:
        return {}
    return models.CorpTaxHistory.sync_all_corps()


@api.get(
    "corp/tax/list",
    tags=["Corporation Taxes"],
)
def get_corp_tax_data(request, days=90, conf_id=1):
    if not request.user.is_superuser:
        return []
    start = timezone.now() - timedelta(days=days)

    t = models.CorpTaxPayoutTaxConfiguration.objects.get(id=conf_id)

    output = []
    for w in t.get_payment_data(start_date=start):
        output.append(
            {
                "corporation": w.division.corporation.corporation.corporation_name,
                "id": w.entry_id,
                "date": w.date,
                "first_party": {
                    "id": w.first_party_id,
                    "name": w.first_party_name.name,
                    "cat": w.first_party_name.category,
                },
                "second_party":  {
                    "id": w.second_party_id,
                    "name": w.second_party_name.name,
                    "cat": w.second_party_name.category,
                },
                "ref_type": w.ref_type,
                "amount": w.amount,
                "reason": w.reason,
                "description": w.description,
            }
        )

    return output


@api.get(
    "corp/tax/aggregates",
    tags=["Corporation Taxes"],
)
def get_corp_tax_aggregates(request, days=90, conf_id=1):
    if not request.user.is_superuser:
        return []
    start = timezone.now() - timedelta(days=days)
    t = models.CorpTaxPayoutTaxConfiguration.objects.get(id=conf_id)
    tx = t.get_aggregates(start_date=start, full=False)
    return tx


@api.get(
    "corp/member/count",
    tags=["Corporation Taxes"],
)
def get_corp_member_count(request, conf_id=1):
    if not request.user.is_superuser:
        return []
    t = models.CorpTaxPerMemberTaxConfiguration.objects.get(id=conf_id)
    tx = t.get_main_counts()
    output = {}
    for crp in tx:
        output[crp['corp_name']] = crp['character_id__count']
    return output


@api.get(
    "corp/member/tax",
    tags=["Corporation Taxes"],
)
def get_corp_member_tax(request, conf_id=1):
    if not request.user.is_superuser:
        return []
    t = models.CorpTaxPerMemberTaxConfiguration.objects.get(id=conf_id)
    tx = t.get_invoice_data()
    return tx


@api.get(
    "corp/member/tax/aggregate",
    tags=["Corporation Taxes"],
)
def get_corp_member_tax__aggregates(request, conf_id=1):
    if not request.user.is_superuser:
        return []
    t = models.CorpTaxPerMemberTaxConfiguration.objects.get(id=conf_id)
    tx = t.get_invoice_stats()
    return tx


@api.get(
    "global/corp/tax/aggregates",
    tags=["Global Taxes"],
)
def get_global_corp_taxes(request, days=90, conf_id=1, alli_filter: int = None):
    if not request.user.is_superuser:
        return []
    start = timezone.now() - timedelta(days=days)
    t = models.CorpTaxConfiguration.objects.get(id=conf_id)
    tx = t.calculate_tax(start_date=start, alliance_filter=alli_filter)

    return tx
