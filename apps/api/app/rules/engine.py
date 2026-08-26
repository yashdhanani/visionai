from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.engine import Event, get_event_engine

logger = logging.getLogger("visionai.rules")


@dataclass
class Rule:
    id: str
    name: str
    condition: Callable[[dict], bool]
    action: Callable[[dict], None]
    cooldown: float = 0.0
    last_fired: float = 0.0
    enabled: bool = True


class RuleEngine:
    def __init__(self):
        self.rules: list[Rule] = []

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def evaluate(self, context: dict) -> None:
        import time
        now = time.time()
        for rule in self.rules:
            if not rule.enabled:
                continue
            if now - rule.last_fired < rule.cooldown:
                continue
            try:
                if rule.condition(context):
                    rule.action(context)
                    rule.last_fired = now
                    logger.info(f"Rule fired: {rule.name}")
            except Exception as e:
                logger.exception(f"Rule evaluation failed: {e}")

    def evaluate_event(self, event: Event) -> None:
        context = {"event": event.__dict__}
        self.evaluate(context)


def create_rule_from_config(config: dict) -> Rule:
    # Simplified: expects a condition function and action function
    # For production, we'd parse expressions
    condition = config.get("condition", lambda ctx: True)
    action = config.get("action", lambda ctx: None)
    return Rule(
        id=config.get("id", "rule_1"),
        name=config.get("name", "Default Rule"),
        condition=condition,
        action=action,
        cooldown=config.get("cooldown", 0.0),
    )


_rule_engine = RuleEngine()


def get_rule_engine() -> RuleEngine:
    return _rule_engine