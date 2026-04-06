#!/usr/bin/env python3
"""Programmatic grading script for yaml-vs-json-parsing evals 1-14.

Usage:
    python programmatic_grade.py <results_dir>

    results_dir should contain eval-{ID}-{format}/ directories,
    each with an output file (output.yaml, output.json, output.md, etc.)
"""
import argparse
import json
import os
import sys

import yaml


def load_output(eval_dir, fmt):
    """Load and parse the output file from an eval directory.
    Returns (parsed_data, raw_text, file_path, error).
    """
    # Try various output file names
    candidates = []
    if fmt == "yaml":
        candidates = ["output.yaml", "output.yml", "output"]
    elif fmt == "json":
        candidates = ["output.json", "output"]
    else:
        candidates = ["output.yaml", "output.yml", "output.json", "output", "output.md"]

    for name in candidates:
        path = os.path.join(eval_dir, name)
        if os.path.exists(path):
            with open(path, "r") as f:
                raw = f.read()
            try:
                if name.endswith(".json") or (fmt == "json" and not name.endswith((".yaml", ".yml", ".md"))):
                    data = json.loads(raw)
                elif name.endswith(".md"):
                    return None, raw, path, None
                else:
                    data = yaml.safe_load(raw)
                return data, raw, path, None
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                return None, raw, path, str(e)
    return None, None, None, "No output file found"


def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def grade_eval_1(data, raw, fmt):
    checks = []
    schemas = data.get("components", {}).get("schemas", {})
    user = schemas.get("User", {})
    paths = data.get("paths", {})

    # Check GET /users/{userId} description
    get_user = paths.get("/users/{userId}", {}).get("get", {})
    desc = get_user.get("description", "")
    checks.append(check("GET /users/{userId} description",
                         desc == "Retrieves a single user by their unique identifier.",
                         f"got '{desc}'"))

    # Check email format
    email_field = user.get("properties", {}).get("email", {})
    checks.append(check("User.email format email",
                         email_field.get("format") == "email",
                         f"format='{email_field.get('format')}'"))

    # Check age type
    age_field = user.get("properties", {}).get("age", {})
    checks.append(check("User.age type number",
                         age_field.get("type") == "number",
                         f"type='{age_field.get('type')}'"))

    # Check createdAt
    created = user.get("properties", {}).get("createdAt", {})
    checks.append(check("createdAt type + date-time",
                         created.get("type") == "string" and created.get("format") == "date-time",
                         str(created)))

    # Check createdAt required
    required = user.get("required", [])
    checks.append(check("createdAt in User.required",
                         "createdAt" in required,
                         f"required={required}"))

    # Check limit description
    get_users = paths.get("/users", {}).get("get", {})
    limit_desc = ""
    for p in get_users.get("parameters", []):
        if p.get("name") == "limit":
            limit_desc = p.get("description", "")
    checks.append(check("GET /users limit description",
                         limit_desc == "Maximum number of users to return per page.",
                         f"got '{limit_desc}'"))
    return checks


def grade_eval_2(data, raw, fmt):
    checks = []
    schemas = data.get("components", {}).get("schemas", {})
    paths = data.get("paths", {})

    # POST /orders summary
    post_orders = paths.get("/orders", {}).get("post", {})
    summary = post_orders.get("summary", "")
    checks.append(check("POST /orders summary exact",
                         summary == "Submit a new customer order.",
                         f"got '{summary}' expected 'Submit a new customer order.'"))

    # OrderItem.quantity type number
    oi = schemas.get("OrderItem", {}).get("properties", {}).get("quantity", {})
    checks.append(check("OrderItem.quantity type number",
                         oi.get("type") == "number",
                         f"type='{oi.get('type')}'"))

    # OrderItem.quantity minimum 0.1
    checks.append(check("OrderItem.quantity minimum 0.1",
                         oi.get("minimum") == 0.1,
                         f"minimum={oi.get('minimum')}"))

    # GET /products/legacy no deprecated
    legacy = paths.get("/products/legacy", {}).get("get", {})
    checks.append(check("GET /products/legacy no deprecated",
                         "deprecated" not in legacy,
                         "ok" if "deprecated" not in legacy else f"deprecated={legacy.get('deprecated')}"))

    # Order.status enum
    status_enum = schemas.get("Order", {}).get("properties", {}).get("status", {}).get("enum", [])
    expected_enum = ["pending", "confirmed", "in_transit", "fulfilled", "cancelled"]
    checks.append(check("Order.status enum exact",
                         status_enum == expected_enum,
                         f"got {status_enum}"))

    # DELETE /users/{userId} x-internal
    delete_user = paths.get("/users/{userId}", {}).get("delete", {})
    checks.append(check("DELETE /users/{userId} x-internal",
                         delete_user.get("x-internal") is True,
                         f"x-internal={delete_user.get('x-internal')}"))
    return checks


def grade_eval_3(data, raw, fmt):
    checks = []
    info = data.get("info", {})
    schemas = data.get("components", {}).get("schemas", {})
    paths = data.get("paths", {})

    checks.append(check("info.title",
                         info.get("title") == "Acme Commerce Platform API",
                         f"got '{info.get('title')}'"))

    checks.append(check("info.version",
                         info.get("version") == "2.0.0",
                         f"got '{info.get('version')}'"))

    # productId parameter description
    get_product = paths.get("/products/{productId}", {}).get("get", {})
    pid_desc = ""
    for p in get_product.get("parameters", []):
        if p.get("name") == "productId":
            pid_desc = p.get("description", "")
    # Also check path-level params
    if not pid_desc:
        for p in paths.get("/products/{productId}", {}).get("parameters", []):
            if p.get("name") == "productId":
                pid_desc = p.get("description", "")
    checks.append(check("productId parameter description",
                         pid_desc == "The globally unique identifier of the product.",
                         f"got '{pid_desc}'"))

    # CreateUserRequest username constraints
    cur = schemas.get("CreateUserRequest", {}).get("properties", {}).get("username", {})
    checks.append(check("CreateUserRequest.username minLength",
                         cur.get("minLength") == 5,
                         f"minLength={cur.get('minLength')}"))
    checks.append(check("CreateUserRequest.username maxLength",
                         cur.get("maxLength") == 32,
                         f"maxLength={cur.get('maxLength')}"))

    # User.middleName nullable
    mn = schemas.get("User", {}).get("properties", {}).get("middleName", {})
    checks.append(check("User.middleName nullable true",
                         mn.get("nullable") is True,
                         f"nullable={mn.get('nullable')}"))
    return checks


def grade_eval_4(data, raw, fmt):
    checks = []
    schemas = data.get("components", {}).get("schemas", {})

    # Product.tagMap
    product = schemas.get("Product", {})
    tag_map = product.get("properties", {}).get("tagMap", {})
    checks.append(check("Product.tagMap type object with additionalProperties.type string",
                         tag_map.get("type") == "object" and
                         tag_map.get("additionalProperties", {}).get("type") == "string",
                         f"tagMap={tag_map}"))

    checks.append(check("Product no tags field",
                         "tags" not in product.get("properties", {}),
                         "ok" if "tags" not in product.get("properties", {}) else "tags still present"))

    # Order.lineItems
    order = schemas.get("Order", {})
    li = order.get("properties", {}).get("lineItems", {})
    li_ref = li.get("additionalProperties", {}).get("$ref", "")
    checks.append(check("Order.lineItems additionalProperties.$ref OrderItem",
                         li.get("type") == "object" and li_ref == "#/components/schemas/OrderItem",
                         f"lineItems={li}"))

    checks.append(check("Order no items field",
                         "items" not in order.get("properties", {}),
                         "ok" if "items" not in order.get("properties", {}) else "items still present"))

    order_req = order.get("required", [])
    checks.append(check("Order required has lineItems not items",
                         "lineItems" in order_req and "items" not in order_req,
                         f"required={order_req}"))

    # UserListResponse.users
    ulr = schemas.get("UserListResponse", {})
    users_field = ulr.get("properties", {}).get("users", {})
    users_ref = users_field.get("additionalProperties", {}).get("$ref", "")
    checks.append(check("UserListResponse.users additionalProperties.$ref User",
                         users_field.get("type") == "object" and users_ref == "#/components/schemas/User",
                         f"users={users_field}"))

    checks.append(check("UserListResponse no data field",
                         "data" not in ulr.get("properties", {}),
                         "ok" if "data" not in ulr.get("properties", {}) else "data still present"))

    ulr_req = ulr.get("required", [])
    checks.append(check("UserListResponse required has users not data",
                         "users" in ulr_req and "data" not in ulr_req,
                         f"required={ulr_req}"))

    # User.role oneOf
    role = schemas.get("User", {}).get("properties", {}).get("role", {})
    one_of = role.get("oneOf", [])
    checks.append(check("User.role oneOf with 4 entries",
                         len(one_of) == 4 and all("const" in e and "title" in e for e in one_of),
                         f"oneOf={one_of}"))

    checks.append(check("User.role no enum key",
                         "enum" not in role,
                         "ok" if "enum" not in role else f"enum={role.get('enum')}"))
    return checks


def grade_eval_5(data, raw, fmt):
    checks = []
    schemas = data.get("components", {}).get("schemas", {})
    paths = data.get("paths", {})

    # Review schema
    review = schemas.get("Review", {})
    review_props = review.get("properties", {})
    has_all_fields = all(f in review_props for f in ["id", "productId", "userId", "rating", "title", "body", "verified", "createdAt"])
    checks.append(check("Review schema has all fields",
                         has_all_fields,
                         f"fields={list(review_props.keys())}"))

    review_req = review.get("required", [])
    expected_req = {"id", "productId", "userId", "rating", "createdAt"}
    checks.append(check("Review required fields",
                         set(review_req) == expected_req,
                         f"required={review_req}"))

    verified = review_props.get("verified", {})
    checks.append(check("Review.verified boolean default false",
                         verified.get("type") == "boolean" and verified.get("default") is False,
                         f"verified={verified}"))

    # ReviewListResponse
    rlr = schemas.get("ReviewListResponse", {})
    avg = rlr.get("properties", {}).get("averageRating", {})
    checks.append(check("ReviewListResponse.averageRating min 1 max 5",
                         avg.get("minimum") == 1 and avg.get("maximum") == 5,
                         f"averageRating={avg}"))

    # GET /products/{productId}/reviews
    reviews_path = paths.get("/products/{productId}/reviews", {})
    get_reviews = reviews_path.get("get", {})
    checks.append(check("GET /products/{productId}/reviews exists",
                         get_reviews.get("operationId") == "listProductReviews",
                         f"operationId={get_reviews.get('operationId')}"))

    # POST /products/{productId}/reviews
    post_reviews = reviews_path.get("post", {})
    checks.append(check("POST /products/{productId}/reviews exists",
                         post_reviews.get("operationId") == "createReview",
                         f"operationId={post_reviews.get('operationId')}"))

    # POST requestBody rating constraints
    rb_schema = post_reviews.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    rating_field = rb_schema.get("properties", {}).get("rating", {})
    checks.append(check("POST requestBody rating min 1 max 5",
                         rating_field.get("minimum") == 1 and rating_field.get("maximum") == 5,
                         f"rating={rating_field}"))

    # POST requestBody rating required
    rb_required = rb_schema.get("required", [])
    checks.append(check("POST requestBody rating is required",
                         "rating" in rb_required,
                         f"required={rb_required}"))
    return checks


def grade_eval_6(data, raw, fmt):
    checks = []
    info = data.get("info", {})

    checks.append(check("info.title",
                         info.get("title") == "City Library API",
                         f"got '{info.get('title')}'"))
    checks.append(check("info.version",
                         info.get("version") == "1.0.0",
                         f"got '{info.get('version')}'"))
    checks.append(check("info.description",
                         info.get("description") == "API for managing library books and borrowing.",
                         f"got '{info.get('description')}'"))

    servers = data.get("servers", [])
    checks.append(check("server url",
                         len(servers) >= 1 and servers[0].get("url") == "https://api.citylibrary.example.com/v1",
                         f"servers={servers}"))

    schemas = data.get("components", {}).get("schemas", {})

    # Book schema
    book = schemas.get("Book", {})
    book_props = book.get("properties", {})
    expected_book_fields = {"id", "isbn", "title", "author", "genre", "availableCopies", "totalCopies"}
    checks.append(check("Book schema has all 7 fields",
                         expected_book_fields.issubset(set(book_props.keys())),
                         f"fields={list(book_props.keys())}"))

    book_req = set(book.get("required", []))
    checks.append(check("Book required fields",
                         book_req == expected_book_fields,
                         f"required={book.get('required', [])}"))

    # BorrowRecord
    br = schemas.get("BorrowRecord", {})
    br_props = br.get("properties", {})
    rd = br_props.get("returnDate", {})
    checks.append(check("BorrowRecord.returnDate nullable true",
                         rd.get("nullable") is True,
                         f"returnDate={rd}"))

    br_req = set(br.get("required", []))
    expected_br_req = {"id", "bookId", "borrowerName", "borrowDate", "dueDate"}
    checks.append(check("BorrowRecord required fields",
                         br_req == expected_br_req,
                         f"required={br.get('required', [])}"))

    paths = data.get("paths", {})
    # GET /books
    get_books = paths.get("/books", {}).get("get", {})
    checks.append(check("GET /books operationId listBooks",
                         get_books.get("operationId") == "listBooks",
                         f"operationId={get_books.get('operationId')}"))

    # POST /books/{bookId}/borrow
    borrow_path = paths.get("/books/{bookId}/borrow", {})
    post_borrow = borrow_path.get("post", {})
    checks.append(check("POST /books/{bookId}/borrow operationId borrowBook",
                         post_borrow.get("operationId") == "borrowBook",
                         f"operationId={post_borrow.get('operationId')}"))

    # borrowerName required in requestBody
    rb = post_borrow.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    checks.append(check("POST borrow requestBody borrowerName required",
                         "borrowerName" in rb.get("required", []),
                         f"required={rb.get('required', [])}"))
    return checks


def grade_eval_7(data, raw, fmt):
    """Grade markdown documentation extraction."""
    checks = []

    # For eval 7, output is markdown, not structured data
    lines = raw.strip().split("\n") if raw else []

    # Check schemas present
    expected_schemas = ["Address", "CreateOrderRequest", "CreateUserRequest", "Dimensions",
                       "ErrorResponse", "Order", "OrderItem", "OrderListResponse",
                       "Product", "ProductListResponse", "UpdateUserRequest", "User",
                       "UserListResponse", "UserPreferences"]

    found_schemas = [l.replace("## ", "").strip() for l in lines if l.startswith("## ")]
    checks.append(check("All 14 schemas present",
                         set(expected_schemas).issubset(set(found_schemas)),
                         f"found {len(found_schemas)} schemas: {found_schemas}"))

    # Check alphabetical order
    checks.append(check("Schemas in alphabetical order",
                         found_schemas == sorted(found_schemas),
                         f"order={'correct' if found_schemas == sorted(found_schemas) else 'incorrect: ' + str(found_schemas[:5]) + '...'}"))

    # First schema should be Address
    checks.append(check("First schema is Address",
                         len(found_schemas) > 0 and found_schemas[0] == "Address",
                         f"first={found_schemas[0] if found_schemas else 'none'}"))

    # Check User schema has expected fields
    user_section = False
    user_fields = []
    for line in lines:
        if line.strip() == "## User":
            user_section = True
            continue
        elif line.startswith("## "):
            if user_section:
                user_section = False
        if user_section and line.startswith("| ") and not line.startswith("| Field") and not line.startswith("|---"):
            field_name = line.split("|")[1].strip()
            if field_name:
                user_fields.append(field_name)

    expected_user_fields = ["age", "createdAt", "email", "firstName", "id", "lastName",
                           "metadata", "middleName", "preferences", "role", "username"]
    checks.append(check("User schema fields alphabetical",
                         user_fields == expected_user_fields,
                         f"fields={user_fields}"))

    # Check $ref types shown correctly
    checks.append(check("$ref types show schema name",
                         "UserPreferences" in raw,
                         "UserPreferences found" if "UserPreferences" in raw else "UserPreferences not found"))

    # Check Required column
    checks.append(check("Required Yes/No present",
                         "| Yes |" in raw and "| No |" in raw,
                         "both Yes and No found" if "| Yes |" in raw and "| No |" in raw else "missing"))

    # Check array types
    checks.append(check("Array types formatted correctly",
                         "array of" in raw.lower(),
                         "array of type found" if "array of" in raw.lower() else "not found"))
    return checks


def grade_eval_8(data, raw, fmt):
    checks = []

    # No $ref anywhere
    has_ref = "$ref" in raw if raw else True
    checks.append(check("No $ref in document",
                         not has_ref,
                         "no $ref found" if not has_ref else "$ref still present"))

    schemas = data.get("components", {}).get("schemas", {}) if data else {}

    # UserListResponse.data.items has User properties inline
    ulr_data = schemas.get("UserListResponse", {}).get("properties", {}).get("data", {})
    ulr_items = ulr_data.get("items", {})
    checks.append(check("UserListResponse.data.items has username inline",
                         "username" in ulr_items.get("properties", {}),
                         f"items keys={list(ulr_items.get('properties', {}).keys())[:5]}"))

    # Order.items.items has OrderItem inline
    order_items = schemas.get("Order", {}).get("properties", {}).get("items", {})
    oi_items = order_items.get("items", {})
    checks.append(check("Order.items.items has productId inline",
                         "productId" in oi_items.get("properties", {}),
                         f"items keys={list(oi_items.get('properties', {}).keys())}"))

    # Product.dimensions has Dimensions inline
    dims = schemas.get("Product", {}).get("properties", {}).get("dimensions", {})
    checks.append(check("Product.dimensions has width inline",
                         "width" in dims.get("properties", {}),
                         f"dims keys={list(dims.get('properties', {}).keys())}"))

    # GET /users/{userId} 200 response has User inline
    paths = data.get("paths", {}) if data else {}
    get_user_resp = paths.get("/users/{userId}", {}).get("get", {}).get("responses", {}).get("200", {})
    resp_schema = get_user_resp.get("content", {}).get("application/json", {}).get("schema", {})
    checks.append(check("GET /users/{userId} 200 has User inline",
                         "username" in resp_schema.get("properties", {}),
                         f"schema keys={list(resp_schema.get('properties', {}).keys())[:5]}"))

    # BadRequest response inlined
    br = data.get("components", {}).get("responses", {}).get("BadRequest", {}) if data else {}
    br_schema = br.get("content", {}).get("application/json", {}).get("schema", {})
    checks.append(check("BadRequest response has ErrorResponse inline",
                         "code" in br_schema.get("properties", {}) or "message" in br_schema.get("properties", {}),
                         f"schema keys={list(br_schema.get('properties', {}).keys())}"))
    return checks


def grade_eval_9(data, raw, fmt):
    checks = []
    schemas = data.get("components", {}).get("schemas", {})
    paths = data.get("paths", {})

    # Payment schema
    payment = schemas.get("Payment", {})
    payment_props = payment.get("properties", {})
    expected_fields = {"id", "orderId", "amount", "currency", "method", "status", "processedAt"}
    checks.append(check("Payment schema has all 7 fields",
                         expected_fields.issubset(set(payment_props.keys())),
                         f"fields={list(payment_props.keys())}"))

    payment_req = set(payment.get("required", []))
    checks.append(check("Payment required fields",
                         payment_req == {"id", "orderId", "amount", "currency", "method", "status"},
                         f"required={payment.get('required', [])}"))

    # Refund schema
    refund = schemas.get("Refund", {})
    refund_props = refund.get("properties", {})
    checks.append(check("Refund schema has all 5 fields",
                         {"id", "paymentId", "amount", "reason", "createdAt"}.issubset(set(refund_props.keys())),
                         f"fields={list(refund_props.keys())}"))

    # Payments tag
    tags = data.get("tags", [])
    has_payments_tag = any(t.get("name") == "payments" for t in tags)
    checks.append(check("payments tag exists",
                         has_payments_tag,
                         f"tags={[t.get('name') for t in tags]}"))

    # POST /orders/{orderId}/payments
    order_payments = paths.get("/orders/{orderId}/payments", {})
    post_payment = order_payments.get("post", {})
    checks.append(check("POST /orders/{orderId}/payments createPayment",
                         post_payment.get("operationId") == "createPayment",
                         f"operationId={post_payment.get('operationId')}"))

    # GET /orders/{orderId}/payments
    get_payments = order_payments.get("get", {})
    checks.append(check("GET /orders/{orderId}/payments listOrderPayments",
                         get_payments.get("operationId") == "listOrderPayments",
                         f"operationId={get_payments.get('operationId')}"))

    # POST /payments/{paymentId}/refund
    refund_path = paths.get("/payments/{paymentId}/refund", {})
    post_refund = refund_path.get("post", {})
    checks.append(check("POST /payments/{paymentId}/refund refundPayment",
                         post_refund.get("operationId") == "refundPayment",
                         f"operationId={post_refund.get('operationId')}"))

    # Original endpoints still exist
    original_endpoints = ["/users", "/users/{userId}", "/products", "/products/{productId}", "/orders"]
    all_present = all(ep in paths for ep in original_endpoints)
    checks.append(check("All original endpoints preserved",
                         all_present,
                         f"paths={list(paths.keys())}"))

    # Original schemas still exist
    original_schemas = ["User", "Product", "Order", "OrderItem", "Address"]
    all_schemas = all(s in schemas for s in original_schemas)
    checks.append(check("All original schemas preserved",
                         all_schemas,
                         f"schemas={list(schemas.keys())}"))

    # createPayment requestBody
    rb = post_payment.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    rb_req = rb.get("required", [])
    checks.append(check("createPayment requestBody amount+method required",
                         "amount" in rb_req and "method" in rb_req,
                         f"required={rb_req}"))
    return checks


def grade_eval_10(data, raw, fmt):
    checks = []
    schemas = data.get("components", {}).get("schemas", {})
    paths = data.get("paths", {})

    # CreateOrderRequest.items.items.properties.quantity.minimum == 2
    cor = schemas.get("CreateOrderRequest", {})
    cor_items = cor.get("properties", {}).get("items", {}).get("items", {})
    qty = cor_items.get("properties", {}).get("quantity", {})
    checks.append(check("CreateOrderRequest quantity minimum 2",
                         qty.get("minimum") == 2,
                         f"minimum={qty.get('minimum')}"))

    # productId maxLength 36
    pid = cor_items.get("properties", {}).get("productId", {})
    checks.append(check("CreateOrderRequest productId maxLength 36",
                         pid.get("maxLength") == 36,
                         f"maxLength={pid.get('maxLength')}"))

    # UserPreferences.notifications.properties.inApp
    up = schemas.get("UserPreferences", {})
    notif = up.get("properties", {}).get("notifications", {}).get("properties", {})
    in_app = notif.get("inApp", {})
    checks.append(check("UserPreferences.notifications.inApp boolean default true",
                         in_app.get("type") == "boolean" and in_app.get("default") is True,
                         f"inApp={in_app}"))

    # ErrorResponse.details.items.properties.code
    er = schemas.get("ErrorResponse", {})
    details_items = er.get("properties", {}).get("details", {}).get("items", {})
    code_field = details_items.get("properties", {}).get("code", {})
    checks.append(check("ErrorResponse.details.items.properties.code string",
                         code_field.get("type") == "string",
                         f"code={code_field}"))

    # GET /orders status enum has 6 values including "returned"
    get_orders = paths.get("/orders", {}).get("get", {})
    status_enum = []
    for p in get_orders.get("parameters", []):
        if p.get("name") == "status":
            status_enum = p.get("schema", {}).get("enum", [])
    checks.append(check("GET /orders status enum has returned",
                         "returned" in status_enum and len(status_enum) >= 5,
                         f"enum={status_enum}"))

    # GET /users 200 response x-rate-limit
    get_users_200 = paths.get("/users", {}).get("get", {}).get("responses", {}).get("200", {})
    checks.append(check("GET /users 200 x-rate-limit 100",
                         get_users_200.get("x-rate-limit") == 100,
                         f"x-rate-limit={get_users_200.get('x-rate-limit')}"))
    return checks


def grade_eval_11(data, raw, fmt):
    checks = []

    # Top-level keys sorted
    if data:
        top_keys = list(data.keys())
        checks.append(check("Top-level keys sorted",
                             top_keys == sorted(top_keys),
                             f"keys={top_keys}"))

        # Info keys sorted
        info_keys = list(data.get("info", {}).keys())
        checks.append(check("info keys sorted",
                             info_keys == sorted(info_keys),
                             f"keys={info_keys}"))

        # Path keys sorted
        path_keys = list(data.get("paths", {}).keys())
        checks.append(check("path keys sorted",
                             path_keys == sorted(path_keys),
                             f"keys={path_keys}"))

        # User schema keys sorted
        user = data.get("components", {}).get("schemas", {}).get("User", {})
        user_keys = list(user.keys())
        checks.append(check("User schema keys sorted",
                             user_keys == sorted(user_keys),
                             f"keys={user_keys}"))

        # User properties keys sorted
        user_props_keys = list(user.get("properties", {}).keys())
        checks.append(check("User properties keys sorted",
                             user_props_keys == sorted(user_props_keys),
                             f"keys={user_props_keys}"))

        # Check semantic equivalence - all original schemas present
        schemas = data.get("components", {}).get("schemas", {})
        expected = ["User", "Product", "Order", "OrderItem", "Address", "Dimensions"]
        all_present = all(s in schemas for s in expected)
        checks.append(check("All original schemas present (semantic equiv)",
                             all_present,
                             f"schemas={list(schemas.keys())}"))

        # Check all original paths present
        paths = data.get("paths", {})
        expected_paths = ["/users", "/users/{userId}", "/products", "/products/{productId}", "/orders"]
        all_paths = all(p in paths for p in expected_paths)
        checks.append(check("All original paths present",
                             all_paths,
                             f"paths={list(paths.keys())}"))
    else:
        checks.append(check("Document parsed", False, "data is None"))
    return checks


def grade_eval_12(data, raw, fmt):
    checks = []
    schemas = data.get("components", {}).get("schemas", {})

    # Dimensions schema deleted
    checks.append(check("Dimensions schema deleted",
                         "Dimensions" not in schemas,
                         "ok" if "Dimensions" not in schemas else "still present"))

    # Product.dimensions inlined
    dims = schemas.get("Product", {}).get("properties", {}).get("dimensions", {})
    checks.append(check("Product.dimensions has inline properties",
                         "width" in dims.get("properties", {}),
                         f"dims keys={list(dims.get('properties', {}).keys())}"))

    # Address schema deleted
    checks.append(check("Address schema deleted",
                         "Address" not in schemas,
                         "ok" if "Address" not in schemas else "still present"))

    # Order.shippingAddress inlined
    ship_addr = schemas.get("Order", {}).get("properties", {}).get("shippingAddress", {})
    checks.append(check("Order.shippingAddress has inline properties",
                         "street" in ship_addr.get("properties", {}),
                         f"addr keys={list(ship_addr.get('properties', {}).keys())}"))

    # CreateOrderRequest.shippingAddress inlined
    cor_addr = schemas.get("CreateOrderRequest", {}).get("properties", {}).get("shippingAddress", {})
    checks.append(check("CreateOrderRequest.shippingAddress has inline properties",
                         "street" in cor_addr.get("properties", {}),
                         f"addr keys={list(cor_addr.get('properties', {}).keys())}"))

    # UserPreferences schema deleted
    checks.append(check("UserPreferences schema deleted",
                         "UserPreferences" not in schemas,
                         "ok" if "UserPreferences" not in schemas else "still present"))

    # User.preferences inlined
    prefs = schemas.get("User", {}).get("properties", {}).get("preferences", {})
    checks.append(check("User.preferences has inline properties",
                         "theme" in prefs.get("properties", {}),
                         f"prefs keys={list(prefs.get('properties', {}).keys())}"))

    # UpdateUserRequest.preferences inlined
    update_prefs = schemas.get("UpdateUserRequest", {}).get("properties", {}).get("preferences", {})
    checks.append(check("UpdateUserRequest.preferences has inline properties",
                         "theme" in update_prefs.get("properties", {}),
                         f"prefs keys={list(update_prefs.get('properties', {}).keys())}"))

    # No dangling refs
    ref_targets = ["Dimensions", "Address", "UserPreferences"]
    has_dangling = any(f'"#/components/schemas/{t}"' in raw or f"'#/components/schemas/{t}'" in raw
                       or f"$ref: '#/components/schemas/{t}'" in raw
                       or f'$ref: "#/components/schemas/{t}"' in raw
                       for t in ref_targets) if raw else True
    checks.append(check("No dangling $ref to deleted schemas",
                         not has_dangling,
                         "ok" if not has_dangling else "dangling refs found"))
    return checks


def grade_eval_13(data, raw, fmt):
    checks = []
    paths = data.get("paths", {}) if data else {}

    if fmt == "yaml":
        # Check YAML comments
        checks.append(check("Comment # --- User Management --- before /users",
                             "# --- User Management ---" in raw,
                             "found" if "# --- User Management ---" in raw else "not found"))
        checks.append(check("Comment # --- Product Catalog --- before /products",
                             "# --- Product Catalog ---" in raw,
                             "found" if "# --- Product Catalog ---" in raw else "not found"))
        checks.append(check("Comment # --- Order Processing --- before /orders",
                             "# --- Order Processing ---" in raw,
                             "found" if "# --- Order Processing ---" in raw else "not found"))
        checks.append(check("Comment # === Schema Definitions === before schemas",
                             "# === Schema Definitions ===" in raw,
                             "found" if "# === Schema Definitions ===" in raw else "not found"))
    elif fmt == "json":
        # Check x-section-doc
        users_doc = paths.get("/users", {}).get("x-section-doc", "")
        checks.append(check("/users x-section-doc User Management",
                             users_doc == "User Management",
                             f"got '{users_doc}'"))
        products_doc = paths.get("/products", {}).get("x-section-doc", "")
        checks.append(check("/products x-section-doc Product Catalog",
                             products_doc == "Product Catalog",
                             f"got '{products_doc}'"))
        orders_doc = paths.get("/orders", {}).get("x-section-doc", "")
        checks.append(check("/orders x-section-doc Order Processing",
                             orders_doc == "Order Processing",
                             f"got '{orders_doc}'"))
        components_doc = data.get("components", {}).get("x-section-doc", "") if data else ""
        checks.append(check("components x-section-doc Schema Definitions",
                             components_doc == "Schema Definitions",
                             f"got '{components_doc}'"))

    # x-stability on all GET operations
    get_endpoints = [
        ("/users", "get"),
        ("/users/{userId}", "get"),
        ("/products", "get"),
        ("/products/{productId}", "get"),
        ("/products/legacy", "get"),
        ("/orders", "get"),
    ]
    for path, method in get_endpoints:
        op = paths.get(path, {}).get(method, {})
        stability = op.get("x-stability")
        checks.append(check(f"GET {path} x-stability stable",
                             stability == "stable",
                             f"x-stability={stability}"))
    return checks


def grade_eval_14(data, raw, fmt, eval_dir):
    """Grade format conversion eval."""
    checks = []

    # Determine expected output format
    if fmt == "yaml":
        # Input was YAML, output should be JSON
        output_path = os.path.join(eval_dir, "output.json")
        target_fmt = "json"
    else:
        # Input was JSON, output should be YAML
        output_path = os.path.join(eval_dir, "output.yaml")
        if not os.path.exists(output_path):
            output_path = os.path.join(eval_dir, "output.yml")
        target_fmt = "yaml"

    if not os.path.exists(output_path):
        checks.append(check(f"Output file exists in {target_fmt} format", False, f"No {target_fmt} output found"))
        return checks

    with open(output_path, "r") as f:
        out_raw = f.read()

    try:
        if target_fmt == "json":
            out_data = json.loads(out_raw)
        else:
            out_data = yaml.safe_load(out_raw)
    except Exception as e:
        checks.append(check(f"Output is valid {target_fmt}", False, str(e)))
        return checks

    checks.append(check(f"Output is valid {target_fmt}", True, "parsed successfully"))

    info = out_data.get("info", {})
    checks.append(check("info.title matches",
                         info.get("title") == "Acme Commerce Platform API",
                         f"got '{info.get('title')}'"))
    checks.append(check("info.version matches",
                         info.get("version") == "2.0.0",
                         f"got '{info.get('version')}'"))

    # All paths present
    paths = out_data.get("paths", {})
    expected_paths = ["/users", "/users/{userId}", "/products", "/products/{productId}", "/orders"]
    all_present = all(p in paths for p in expected_paths)
    checks.append(check("All paths present",
                         all_present,
                         f"paths={list(paths.keys())}"))

    # All schemas present
    schemas = out_data.get("components", {}).get("schemas", {})
    expected_schemas = ["User", "Product", "Order", "OrderItem", "Address", "Dimensions"]
    all_schemas = all(s in schemas for s in expected_schemas)
    checks.append(check("All schemas present",
                         all_schemas,
                         f"schemas={list(schemas.keys())}"))

    # User properties
    user = schemas.get("User", {})
    user_req = user.get("required", [])
    user_props = list(user.get("properties", {}).keys())
    checks.append(check("User schema has same properties",
                         "username" in user_props and "email" in user_props and "role" in user_props,
                         f"props={user_props}"))

    # Order.status enum
    order_status = schemas.get("Order", {}).get("properties", {}).get("status", {}).get("enum", [])
    expected_enum = ["pending", "confirmed", "in_transit", "fulfilled", "cancelled"]
    checks.append(check("Order.status enum identical",
                         order_status == expected_enum,
                         f"enum={order_status}"))
    return checks


GRADERS = {
    1: grade_eval_1,
    2: grade_eval_2,
    3: grade_eval_3,
    4: grade_eval_4,
    5: grade_eval_5,
    6: grade_eval_6,
    7: grade_eval_7,
    8: grade_eval_8,
    9: grade_eval_9,
    10: grade_eval_10,
    11: grade_eval_11,
    12: grade_eval_12,
    13: grade_eval_13,
    14: grade_eval_14,
}


def grade_eval_dir(eval_dir, eval_id, fmt):
    """Grade a single eval directory. Returns a run result dict."""
    # Find output file
    output_files = []
    for f in os.listdir(eval_dir):
        if f.startswith("output"):
            output_files.append(f)

    if not output_files:
        return {
            "path": eval_dir,
            "eval_id": eval_id,
            "error": "No output file found",
            "passed": 0,
            "failed": 1,
            "total": 1,
            "pass_rate": 0.0,
            "checks": [check("output file exists", False, "No output file found")],
            "format": fmt,
        }

    # For eval 14, handle specially
    if eval_id == 14:
        # Load based on opposite format
        if fmt == "yaml":
            target = "output.json"
        else:
            target = "output.yaml"
            if target not in output_files:
                target = "output.yml"

        if target in output_files:
            output_path = os.path.join(eval_dir, target)
        else:
            # Might not have correct name
            output_path = os.path.join(eval_dir, output_files[0])

        try:
            eval_checks = grade_eval_14(None, None, fmt, eval_dir)
        except Exception as e:
            return {
                "path": eval_dir,
                "eval_id": eval_id,
                "error": str(e),
                "passed": 0,
                "failed": 1,
                "total": 1,
                "pass_rate": 0.0,
                "checks": [check("grading error", False, str(e))],
                "format": fmt,
            }
    elif eval_id == 7:
        # Markdown output
        md_file = None
        for f in output_files:
            if f.endswith(".md"):
                md_file = f
                break
        if not md_file:
            md_file = output_files[0]

        output_path = os.path.join(eval_dir, md_file)
        with open(output_path, "r") as fh:
            raw = fh.read()
        try:
            eval_checks = grade_eval_7(None, raw, fmt)
        except Exception as e:
            return {
                "path": output_path,
                "eval_id": eval_id,
                "error": str(e),
                "passed": 0,
                "failed": 1,
                "total": 1,
                "pass_rate": 0.0,
                "checks": [check("grading error", False, str(e))],
                "format": fmt,
            }
    else:
        # Standard structured output
        # Pick the right output file
        preferred = f"output.{fmt}" if fmt in ("yaml", "json") else output_files[0]
        if preferred not in output_files:
            preferred = output_files[0]

        output_path = os.path.join(eval_dir, preferred)
        with open(output_path, "r") as fh:
            raw = fh.read()

        try:
            if preferred.endswith(".json") or fmt == "json":
                data = json.loads(raw)
            else:
                data = yaml.safe_load(raw)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            error_msg = str(e)
            # Determine expected check count
            return {
                "path": output_path,
                "eval_id": eval_id,
                "error": error_msg,
                "passed": 0,
                "failed": 1,
                "total": 1,
                "pass_rate": 0.0,
                "checks": [check("document parses (YAML/JSON)", False, error_msg)],
                "format": fmt,
            }

        grader = GRADERS.get(eval_id)
        if not grader:
            return {
                "path": output_path,
                "eval_id": eval_id,
                "error": f"No grader for eval {eval_id}",
                "passed": 0,
                "failed": 1,
                "total": 1,
                "pass_rate": 0.0,
                "checks": [check("grader exists", False, f"No grader for eval {eval_id}")],
                "format": fmt,
            }

        try:
            eval_checks = grader(data, raw, fmt)
        except Exception as e:
            return {
                "path": output_path,
                "eval_id": eval_id,
                "error": str(e),
                "passed": 0,
                "failed": 1,
                "total": 1,
                "pass_rate": 0.0,
                "checks": [check("grading error", False, str(e))],
                "format": fmt,
            }

    passed = sum(1 for c in eval_checks if c["passed"])
    failed = len(eval_checks) - passed
    total = len(eval_checks)

    return {
        "path": output_path if eval_id != 14 else eval_dir,
        "eval_id": eval_id,
        "passed": passed,
        "failed": failed,
        "total": total,
        "pass_rate": passed / total if total > 0 else 0.0,
        "checks": eval_checks,
        "format": fmt,
    }


def main():
    parser = argparse.ArgumentParser(description="Programmatic grading for yaml-vs-json evals")
    parser.add_argument("results_dir", help="Directory containing eval-{ID}-{format}/ subdirs")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    args = parser.parse_args()

    results_dir = args.results_dir
    if not os.path.isdir(results_dir):
        print(f"Error: {results_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    runs = []
    for entry in sorted(os.listdir(results_dir)):
        if not entry.startswith("eval-"):
            continue
        parts = entry.split("-")
        if len(parts) < 3:
            continue
        try:
            eval_id = int(parts[1])
        except ValueError:
            continue
        fmt = parts[2]
        if fmt not in ("yaml", "json"):
            continue

        eval_dir = os.path.join(results_dir, entry)
        if not os.path.isdir(eval_dir):
            continue

        result = grade_eval_dir(eval_dir, eval_id, fmt)
        runs.append(result)

    # Aggregate
    total_passed = sum(r["passed"] for r in runs)
    total_assertions = sum(r["total"] for r in runs)

    yaml_runs = [r for r in runs if r["format"] == "yaml"]
    json_runs = [r for r in runs if r["format"] == "json"]

    yaml_pass_rate = sum(r["pass_rate"] for r in yaml_runs) / len(yaml_runs) if yaml_runs else 0
    json_pass_rate = sum(r["pass_rate"] for r in json_runs) / len(json_runs) if json_runs else 0

    output = {
        "root": os.path.abspath(results_dir),
        "assertions_passed": total_passed,
        "assertions_total": total_assertions,
        "overall_pass_rate": total_passed / total_assertions if total_assertions > 0 else 0.0,
        "yaml_mean_pass_rate": yaml_pass_rate,
        "json_mean_pass_rate": json_pass_rate,
        "runs": runs,
    }

    output_path = args.output or os.path.join(os.path.dirname(results_dir), f"programmatic_grade_{os.path.basename(results_dir)}.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Grading complete: {total_passed}/{total_assertions} assertions passed ({output['overall_pass_rate']:.1%})")
    print(f"  YAML mean pass rate: {yaml_pass_rate:.1%}")
    print(f"  JSON mean pass rate: {json_pass_rate:.1%}")
    print(f"Results written to: {output_path}")


if __name__ == "__main__":
    main()
