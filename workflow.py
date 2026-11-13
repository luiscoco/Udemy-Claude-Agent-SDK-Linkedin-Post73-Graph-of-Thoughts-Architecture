"""Lesson-specific workflow. Read this file before the execution adapter."""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from runtime import atomic_json, contained_path, in_process_tool

async def run(agent, data):
    proposals = await asyncio.gather(
        agent.ask('transit', 'Propose actions from the cost catalogue.', data, {'actions': ['bus_priority', 'bike_lane']}),
        agent.ask('access', 'Propose complementary actions from the cost catalogue.', data, {'actions': ['bike_lane', 'parking_fee']}))
    nodes, edges = {}, []
    for index, proposal in enumerate(proposals):
        for action in proposal['actions']:
            if action not in data['costs']:
                raise ValueError('Unknown action in proposal graph')
            nodes.setdefault(action, {'cost': data['costs'][action], 'proposers': []})['proposers'].append(index)
            edges.append({'from': 'proposal_' + str(index), 'to': action})
    selected, cost = [], 0
    for action in sorted(nodes, key=lambda a: (-len(nodes[a]['proposers']), nodes[a]['cost'], a)):
        if cost + nodes[action]['cost'] <= data['budget']:
            selected.append(action)
            cost += nodes[action]['cost']
    return {'nodes': nodes, 'edges': edges, 'selected': selected, 'cost': cost, 'merge_rule': 'Identical action IDs share a node; distinct ideas are not silently equated.'}
