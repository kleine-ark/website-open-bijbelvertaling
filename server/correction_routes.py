"""HTTP surface: reviewers can request and decide, never impersonate the AI/operator."""
import re


def route(handler, method, path, query, actor):
    if not path.startswith('/api/collaboration/corrections'):
        return False
    handler.app['store']._require_role(actor, 'reviewer')
    handler._sync_catalog()
    service = handler.app['corrections']
    if path == '/api/collaboration/corrections':
        if method == 'GET':
            handler._write_json(200, service.list(actor, handler._one(query, 'status'),
                handler._one(query, 'q'), handler._integer(query, 'offset', 0), handler._integer(query, 'limit', 50)))
            return True
        if method == 'POST':
            handler._write_json(201, {'correction': service.create(actor, handler._body())})
            return True
    match = re.fullmatch(r'/api/collaboration/corrections/([a-f0-9-]{36})(/decision)?', path)
    if match:
        if method == 'GET' and not match[2]:
            handler._write_json(200, {'correction': service.get(actor, match[1])})
            return True
        if method == 'POST' and match[2]:
            handler._write_json(200, {'correction': service.decide(actor, match[1], handler._body())})
            return True
    return False
