#!/usr/bin/env python3
"""Programmatically grade OpenAPI mutation outputs for evals 1–3 (yaml-vs-json experiment)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as e:
    print("Requires PyYAML: pip install pyyaml", file=sys.stderr)
    raise SystemExit(1) from e

EXPECTED = {
    1: {
        "user_desc": "Retrieves a single user by their unique identifier.",
        "limit_desc": "Maximum number of users to return per page.",
    },
    2: {
        "post_orders_summary": "Submit a new customer order.",
        "order_status": [
            "pending",
            "confirmed",
            "in_transit",
            "fulfilled",
            "cancelled",
        ],
    },
    3: {
        "title": "Acme Commerce Platform API",
        "version": "2.0.0",
        "product_id_desc": "The globally unique identifier of the product.",
        "username_min": 5,
        "username_max": 32,
    },
}


def load_spec(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Root must be object, got {type(data)}")
    return data


def has_key_recursive(obj: Any, key: str) -> bool:
    if isinstance(obj, dict):
        if key in obj:
            return True
        return any(has_key_recursive(v, key) for v in obj.values())
    if isinstance(obj, list):
        return any(has_key_recursive(v, key) for v in obj)
    return False


def param_by_name(params: list[dict[str, Any]] | None, name: str) -> dict[str, Any] | None:
    if not params:
        return None
    for p in params:
        if p.get("name") == name:
            return p
    return None


def schemas(spec: dict[str, Any]) -> dict[str, Any]:
    return spec.get("components", {}).get("schemas", {})


def check_eval_1(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    paths = spec.get("paths", {})
    u = paths.get("/users/{userId}", {}).get("get", {})
    d = u.get("description")
    out.append(
        (
            "GET /users/{userId} description",
            d == EXPECTED[1]["user_desc"],
            f"got {d!r}",
        )
    )
    su = schemas(spec).get("User", {})
    props = su.get("properties", {})
    email = props.get("email", {})
    out.append(
        (
            "User.email format email",
        email.get("format") == "email",
        f"format={email.get('format')!r}",
        )
    )
    age = props.get("age", {})
    out.append(
        (
            "User.age type number",
            age.get("type") == "number",
            f"type={age.get('type')!r}",
        )
    )
    ca = props.get("createdAt", {})
    out.append(
        (
            "createdAt type + date-time",
            ca.get("type") == "string" and ca.get("format") == "date-time",
            f"{ca!r}",
        )
    )
    req = su.get("required") or []
    out.append(
        (
            "createdAt in User.required",
            "createdAt" in req,
            f"required={req!r}",
        )
    )
    lu = paths.get("/users", {}).get("get", {})
    lim = param_by_name(lu.get("parameters"), "limit")
    ld = (lim or {}).get("description")
    out.append(
        (
            "GET /users limit description",
            ld == EXPECTED[1]["limit_desc"],
            f"got {ld!r}",
        )
    )
    return out


def check_eval_2(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    paths = spec.get("paths", {})
    post = paths.get("/orders", {}).get("post", {})
    summ = post.get("summary")
    exp = EXPECTED[2]["post_orders_summary"]
    out.append(
        (
            "POST /orders summary exact",
            summ == exp,
            f"got {summ!r} expected {exp!r}",
        )
    )
    oi = schemas(spec).get("OrderItem", {}).get("properties", {}).get("quantity", {})
    out.append(
        (
            "OrderItem.quantity type number",
            oi.get("type") == "number",
            f"type={oi.get('type')!r}",
        )
    )
    out.append(
        (
            "OrderItem.quantity minimum 0.1",
            oi.get("minimum") == 0.1,
            f"minimum={oi.get('minimum')!r}",
        )
    )
    legacy = paths.get("/products/legacy", {}).get("get", {})
    out.append(
        (
            "GET /products/legacy no deprecated",
            not has_key_recursive(legacy, "deprecated"),
            "deprecated found under operation" if has_key_recursive(legacy, "deprecated") else "ok",
        )
    )
    st = schemas(spec).get("Order", {}).get("properties", {}).get("status", {})
    enum = st.get("enum") or []
    exp_e = EXPECTED[2]["order_status"]
    out.append(
        (
            "Order.status enum exact",
            enum == exp_e,
            f"got {enum!r}",
        )
    )
    del_op = paths.get("/users/{userId}", {}).get("delete", {})
    out.append(
        (
            "DELETE /users/{userId} x-internal",
            del_op.get("x-internal") is True,
            f"x-internal={del_op.get('x-internal')!r}",
        )
    )
    return out


def check_eval_3(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    info = spec.get("info", {})
    out.append(
        (
            "info.title",
            info.get("title") == EXPECTED[3]["title"],
            f"got {info.get('title')!r}",
        )
    )
    out.append(
        (
            "info.version",
            info.get("version") == EXPECTED[3]["version"],
            f"got {info.get('version')!r}",
        )
    )
    paths = spec.get("paths", {})
    gpp = paths.get("/products/{productId}", {}).get("get", {})
    params = gpp.get("parameters") or []
    pid = param_by_name(params, "productId")
    pd = (pid or {}).get("description")
    exp = EXPECTED[3]["product_id_desc"]
    out.append(
        (
            "productId parameter description",
            pd == exp,
            f"got {pd!r}",
        )
    )
    un = (
        schemas(spec)
        .get("CreateUserRequest", {})
        .get("properties", {})
        .get("username", {})
    )
    out.append(
        (
            "CreateUserRequest.username minLength",
            un.get("minLength") == EXPECTED[3]["username_min"],
            f"minLength={un.get('minLength')!r}",
        )
    )
    out.append(
        (
            "CreateUserRequest.username maxLength",
            un.get("maxLength") == EXPECTED[3]["username_max"],
            f"maxLength={un.get('maxLength')!r}",
        )
    )
    mn = schemas(spec).get("User", {}).get("properties", {}).get("middleName", {})
    out.append(
        (
            "User.middleName nullable true",
            mn.get("nullable") is True,
            f"nullable={mn.get('nullable')!r}",
        )
    )
    return out


def check_eval_4(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    # 1. Product.tagMap exists with correct structure
    prod = schemas(spec).get("Product", {}).get("properties", {})
    tm = prod.get("tagMap", {})
    out.append((
        "Product.tagMap type object",
        tm.get("type") == "object",
        f"type={tm.get('type')!r}",
    ))
    ap = tm.get("additionalProperties", {})
    out.append((
        "Product.tagMap additionalProperties string",
        ap.get("type") == "string",
        f"additionalProperties={ap!r}",
    ))
    # 2. Product.tags removed
    out.append((
        "Product.tags removed",
        "tags" not in prod,
        "tags still present" if "tags" in prod else "ok",
    ))
    # 3. Order.lineItems exists
    order = schemas(spec).get("Order", {})
    order_props = order.get("properties", {})
    li = order_props.get("lineItems", {})
    li_ap = li.get("additionalProperties", {})
    out.append((
        "Order.lineItems additionalProperties $ref OrderItem",
        li_ap.get("$ref") == "#/components/schemas/OrderItem",
        f"$ref={li_ap.get('$ref')!r}",
    ))
    # 4. Order.items removed
    out.append((
        "Order.items removed",
        "items" not in order_props,
        "items still present" if "items" in order_props else "ok",
    ))
    # 5. Order.required has lineItems, not items
    order_req = order.get("required", [])
    out.append((
        "Order.required has lineItems not items",
        "lineItems" in order_req and "items" not in order_req,
        f"required={order_req!r}",
    ))
    # 6. UserListResponse.users exists
    ulr = schemas(spec).get("UserListResponse", {})
    ulr_props = ulr.get("properties", {})
    users_f = ulr_props.get("users", {})
    users_ap = users_f.get("additionalProperties", {})
    out.append((
        "UserListResponse.users $ref User",
        users_ap.get("$ref") == "#/components/schemas/User",
        f"$ref={users_ap.get('$ref')!r}",
    ))
    # 7. UserListResponse.data removed
    out.append((
        "UserListResponse.data removed",
        "data" not in ulr_props,
        "data still present" if "data" in ulr_props else "ok",
    ))
    # 8. UserListResponse.required has users not data
    ulr_req = ulr.get("required", [])
    out.append((
        "UserListResponse.required has users not data",
        "users" in ulr_req and "data" not in ulr_req,
        f"required={ulr_req!r}",
    ))
    # 9. User.role has oneOf with 4 entries
    role = schemas(spec).get("User", {}).get("properties", {}).get("role", {})
    one_of = role.get("oneOf", [])
    consts = sorted([e.get("const") for e in one_of if "const" in e])
    expected_consts = ["admin", "guest", "moderator", "user"]
    out.append((
        "User.role oneOf 4 entries with const",
        consts == expected_consts,
        f"oneOf consts={consts!r}",
    ))
    # 10. User.role enum removed
    out.append((
        "User.role enum removed",
        "enum" not in role,
        "enum still present" if "enum" in role else "ok",
    ))
    return out


def check_eval_5(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    sc = schemas(spec)
    # 1. Review schema exists with correct fields
    review = sc.get("Review", {})
    rprops = review.get("properties", {})
    out.append((
        "Review schema has rating with min/max",
        rprops.get("rating", {}).get("type") == "integer"
        and rprops.get("rating", {}).get("minimum") == 1
        and rprops.get("rating", {}).get("maximum") == 5,
        f"rating={rprops.get('rating')!r}",
    ))
    # 2. Review.required
    review_req = sorted(review.get("required", []))
    expected_req = sorted(["id", "productId", "userId", "rating", "createdAt"])
    out.append((
        "Review.required correct",
        review_req == expected_req,
        f"required={review_req!r}",
    ))
    # 3. Review.verified
    verified = rprops.get("verified", {})
    out.append((
        "Review.verified boolean default false",
        verified.get("type") == "boolean" and verified.get("default") is False,
        f"verified={verified!r}",
    ))
    # 4. ReviewListResponse exists with averageRating
    rlr = sc.get("ReviewListResponse", {})
    rlr_props = rlr.get("properties", {})
    avg = rlr_props.get("averageRating", {})
    out.append((
        "ReviewListResponse.averageRating min/max",
        avg.get("minimum") == 1 and avg.get("maximum") == 5,
        f"averageRating={avg!r}",
    ))
    # 5. GET /products/{productId}/reviews exists
    paths = spec.get("paths", {})
    reviews_path = paths.get("/products/{productId}/reviews", {})
    get_rev = reviews_path.get("get", {})
    out.append((
        "GET /products/{productId}/reviews operationId",
        get_rev.get("operationId") == "listProductReviews",
        f"operationId={get_rev.get('operationId')!r}",
    ))
    # 6. POST /products/{productId}/reviews exists
    post_rev = reviews_path.get("post", {})
    out.append((
        "POST /products/{productId}/reviews operationId",
        post_rev.get("operationId") == "createReview",
        f"operationId={post_rev.get('operationId')!r}",
    ))
    # 7. POST requestBody has rating as required
    rb = post_rev.get("requestBody", {})
    rb_schema = (
        rb.get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    rb_req = rb_schema.get("required", [])
    rb_rating = rb_schema.get("properties", {}).get("rating", {})
    out.append((
        "POST requestBody rating required with min/max",
        "rating" in rb_req
        and rb_rating.get("minimum") == 1
        and rb_rating.get("maximum") == 5,
        f"required={rb_req!r}, rating={rb_rating!r}",
    ))
    return out


def check_eval_6(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    info = spec.get("info", {})
    # 1. info.title
    out.append((
        "info.title",
        info.get("title") == "City Library API",
        f"got {info.get('title')!r}",
    ))
    # 2. info.version
    out.append((
        "info.version",
        info.get("version") == "1.0.0",
        f"got {info.get('version')!r}",
    ))
    # 3. info.description
    out.append((
        "info.description",
        info.get("description") == "API for managing library books and borrowing.",
        f"got {info.get('description')!r}",
    ))
    # 4. Server
    servers = spec.get("servers", [])
    out.append((
        "server url",
        len(servers) >= 1
        and servers[0].get("url") == "https://api.citylibrary.example.com/v1",
        f"servers={servers!r}",
    ))
    # 5. Book schema fields
    sc = schemas(spec)
    book = sc.get("Book", {})
    bprops = book.get("properties", {})
    isbn = bprops.get("isbn", {})
    out.append((
        "Book.isbn pattern",
        isbn.get("type") == "string" and isbn.get("pattern") == "^[0-9]{13}$",
        f"isbn={isbn!r}",
    ))
    genre = bprops.get("genre", {})
    expected_enum = ["fiction", "non-fiction", "science", "history", "biography"]
    out.append((
        "Book.genre enum",
        genre.get("enum") == expected_enum,
        f"enum={genre.get('enum')!r}",
    ))
    book_req = sorted(book.get("required", []))
    expected_book_req = sorted(
        ["id", "isbn", "title", "author", "genre", "totalCopies", "availableCopies"]
    )
    out.append((
        "Book.required",
        book_req == expected_book_req,
        f"required={book_req!r}",
    ))
    # 6. BorrowRecord
    br = sc.get("BorrowRecord", {})
    br_props = br.get("properties", {})
    rd = br_props.get("returnDate", {})
    out.append((
        "BorrowRecord.returnDate nullable",
        rd.get("nullable") is True and rd.get("format") == "date",
        f"returnDate={rd!r}",
    ))
    br_req = sorted(br.get("required", []))
    expected_br_req = sorted(["id", "bookId", "borrowerName", "borrowDate", "dueDate"])
    out.append((
        "BorrowRecord.required",
        br_req == expected_br_req,
        f"required={br_req!r}",
    ))
    # 7. Endpoints
    paths = spec.get("paths", {})
    get_books = paths.get("/books", {}).get("get", {})
    out.append((
        "GET /books operationId",
        get_books.get("operationId") == "listBooks",
        f"operationId={get_books.get('operationId')!r}",
    ))
    borrow_path = paths.get("/books/{bookId}/borrow", {})
    post_borrow = borrow_path.get("post", {})
    out.append((
        "POST /books/{bookId}/borrow operationId",
        post_borrow.get("operationId") == "borrowBook",
        f"operationId={post_borrow.get('operationId')!r}",
    ))
    # 8. POST requestBody has borrowerName required
    rb = post_borrow.get("requestBody", {})
    rb_schema = (
        rb.get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    rb_req = rb_schema.get("required", [])
    out.append((
        "POST borrow requestBody borrowerName required",
        "borrowerName" in rb_req,
        f"required={rb_req!r}",
    ))
    return out


def check_eval_7(text: str) -> list[tuple[str, bool, str]]:
    """Grade eval 7 — markdown schema extraction. Takes raw file text, not parsed spec."""
    out: list[tuple[str, bool, str]] = []
    # Expected schemas in alphabetical order
    expected_schemas = [
        "Address", "CreateOrderRequest", "CreateUserRequest", "Dimensions",
        "ErrorResponse", "Order", "OrderItem", "OrderListResponse", "Product",
        "ProductListResponse", "UpdateUserRequest", "User", "UserListResponse",
        "UserPreferences",
    ]
    # 1. Check all schemas present
    found_schemas = re.findall(r"^## (\w+)", text, re.MULTILINE)
    out.append((
        "All 14 schemas present",
        sorted(found_schemas) == expected_schemas,
        f"found {len(found_schemas)}: {sorted(found_schemas)!r}",
    ))
    # 2. Alphabetical order
    out.append((
        "Schemas in alphabetical order",
        found_schemas == expected_schemas,
        f"order: {found_schemas!r}",
    ))
    # 3. Address is first
    out.append((
        "Address is first schema",
        len(found_schemas) > 0 and found_schemas[0] == "Address",
        f"first={found_schemas[0]!r}" if found_schemas else "no schemas found",
    ))
    # 4. User section has key fields (spot-check)
    user_match = re.search(
        r"## User\n(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    user_text = user_match.group(1) if user_match else ""
    user_fields = re.findall(r"^\| (\w+)", user_text, re.MULTILINE)
    # Check some expected fields exist (alphabetical)
    for field in ["age", "email", "id", "role", "username"]:
        out.append((
            f"User table has field {field}",
            field in user_fields,
            f"found fields: {user_fields!r}",
        ))
    # 5. $ref types rendered correctly (User.preferences should mention UserPreferences)
    out.append((
        "User.preferences type shows UserPreferences",
        "UserPreferences" in user_text,
        "UserPreferences ref rendered" if "UserPreferences" in user_text else "not found",
    ))
    # 6. Required fields marked correctly (User.id should be Yes)
    id_line = [l for l in user_text.split("\n") if re.match(r"^\| id\b", l)]
    out.append((
        "User.id marked as required",
        len(id_line) > 0 and "Yes" in id_line[0],
        f"id line: {id_line[0]!r}" if id_line else "id line not found",
    ))
    return out


def check_eval_8(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    """$ref inlining — no $ref should remain anywhere."""
    out: list[tuple[str, bool, str]] = []
    # 1. No $ref anywhere in the document
    out.append((
        "No $ref in document",
        not has_key_recursive(spec, "$ref"),
        "found $ref" if has_key_recursive(spec, "$ref") else "ok",
    ))
    # 2. UserListResponse.data.items should have User properties inlined
    ulr = schemas(spec).get("UserListResponse", {})
    data_items = ulr.get("properties", {}).get("data", {}).get("items", {})
    out.append((
        "UserListResponse.data.items has username (User inlined)",
        "username" in data_items.get("properties", {}),
        f"data.items keys={list(data_items.get('properties', {}).keys())!r}",
    ))
    # 3. Order.items.items should have OrderItem properties inlined
    order = schemas(spec).get("Order", {})
    items_items = order.get("properties", {}).get("items", {}).get("items", {})
    out.append((
        "Order.items.items has productId (OrderItem inlined)",
        "productId" in items_items.get("properties", {}),
        f"items.items keys={list(items_items.get('properties', {}).keys())!r}",
    ))
    # 4. Product.dimensions has Dimensions properties inlined
    prod = schemas(spec).get("Product", {})
    dims = prod.get("properties", {}).get("dimensions", {})
    out.append((
        "Product.dimensions has width (Dimensions inlined)",
        "width" in dims.get("properties", {}),
        f"dimensions keys={list(dims.get('properties', {}).keys())!r}",
    ))
    # 5. GET /users/{userId} 200 response schema has User properties inlined
    paths = spec.get("paths", {})
    get_user_resp = (
        paths.get("/users/{userId}", {})
        .get("get", {})
        .get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    out.append((
        "GET /users/{userId} 200 schema has username (User inlined)",
        "username" in get_user_resp.get("properties", {}),
        f"resp schema keys={list(get_user_resp.get('properties', {}).keys())!r}",
    ))
    # 6. BadRequest response has ErrorResponse inlined
    bad_req = (
        spec.get("components", {})
        .get("responses", {})
        .get("BadRequest", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    out.append((
        "BadRequest response schema has code (ErrorResponse inlined)",
        "code" in bad_req.get("properties", {}),
        f"bad_req schema keys={list(bad_req.get('properties', {}).keys())!r}",
    ))
    return out


def check_eval_9(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    """Spec merging — Payments API merged into existing spec."""
    out: list[tuple[str, bool, str]] = []
    sc = schemas(spec)
    paths = spec.get("paths", {})
    # 1. Payment schema exists with correct required
    payment = sc.get("Payment", {})
    pay_req = sorted(payment.get("required", []))
    expected_pay_req = sorted(["id", "orderId", "amount", "currency", "method", "status"])
    out.append((
        "Payment schema required",
        pay_req == expected_pay_req,
        f"required={pay_req!r}",
    ))
    # 2. Refund schema exists with correct required
    refund = sc.get("Refund", {})
    ref_req = sorted(refund.get("required", []))
    expected_ref_req = sorted(["id", "paymentId", "amount", "createdAt"])
    out.append((
        "Refund schema required",
        ref_req == expected_ref_req,
        f"required={ref_req!r}",
    ))
    # 3. payments tag exists
    tags = spec.get("tags", [])
    tag_names = [t.get("name") for t in tags]
    out.append((
        "payments tag exists",
        "payments" in tag_names,
        f"tags={tag_names!r}",
    ))
    # 4. POST /orders/{orderId}/payments
    pay_path = paths.get("/orders/{orderId}/payments", {})
    post_pay = pay_path.get("post", {})
    out.append((
        "POST /orders/{orderId}/payments operationId",
        post_pay.get("operationId") == "createPayment",
        f"operationId={post_pay.get('operationId')!r}",
    ))
    # 5. GET /orders/{orderId}/payments
    get_pay = pay_path.get("get", {})
    out.append((
        "GET /orders/{orderId}/payments operationId",
        get_pay.get("operationId") == "listOrderPayments",
        f"operationId={get_pay.get('operationId')!r}",
    ))
    # 6. POST /payments/{paymentId}/refund
    refund_path = paths.get("/payments/{paymentId}/refund", {})
    post_refund = refund_path.get("post", {})
    out.append((
        "POST /payments/{paymentId}/refund operationId",
        post_refund.get("operationId") == "refundPayment",
        f"operationId={post_refund.get('operationId')!r}",
    ))
    # 7. Original endpoints preserved
    original_ops = [
        ("/users", "get"), ("/users", "post"),
        ("/users/{userId}", "get"), ("/users/{userId}", "put"), ("/users/{userId}", "delete"),
        ("/products", "get"), ("/products/{productId}", "get"),
        ("/orders", "get"), ("/orders", "post"),
    ]
    preserved = all(paths.get(p, {}).get(m, {}) for p, m in original_ops)
    out.append((
        "All original endpoints preserved",
        preserved,
        f"missing: {[(p, m) for p, m in original_ops if not paths.get(p, {}).get(m, {})]!r}",
    ))
    # 8. Original schemas preserved
    original_schemas = ["User", "Product", "Order", "OrderItem", "Address", "Dimensions"]
    schemas_ok = all(s in sc for s in original_schemas)
    out.append((
        "All original schemas preserved",
        schemas_ok,
        f"missing: {[s for s in original_schemas if s not in sc]!r}",
    ))
    # 9. createPayment requestBody has amount and method required
    rb = post_pay.get("requestBody", {})
    rb_schema = rb.get("content", {}).get("application/json", {}).get("schema", {})
    rb_req = rb_schema.get("required", [])
    out.append((
        "createPayment requestBody has amount+method required",
        "amount" in rb_req and "method" in rb_req,
        f"required={rb_req!r}",
    ))
    # 10. Payment.currency enum
    pay_currency = payment.get("properties", {}).get("currency", {})
    out.append((
        "Payment.currency enum",
        pay_currency.get("enum") == ["USD", "EUR", "GBP"],
        f"enum={pay_currency.get('enum')!r}",
    ))
    return out


def check_eval_10(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    """Deep nesting manipulation."""
    out: list[tuple[str, bool, str]] = []
    sc = schemas(spec)
    # 1. CreateOrderRequest.items.items.properties.quantity.minimum = 2
    cor = sc.get("CreateOrderRequest", {})
    cor_items = cor.get("properties", {}).get("items", {}).get("items", {})
    qty = cor_items.get("properties", {}).get("quantity", {})
    out.append((
        "CreateOrderRequest quantity minimum 2",
        qty.get("minimum") == 2,
        f"minimum={qty.get('minimum')!r}",
    ))
    # 2. CreateOrderRequest.items.items.properties.productId.maxLength = 36
    pid = cor_items.get("properties", {}).get("productId", {})
    out.append((
        "CreateOrderRequest productId maxLength 36",
        pid.get("maxLength") == 36,
        f"maxLength={pid.get('maxLength')!r}",
    ))
    # 3. UserPreferences.notifications.properties.inApp
    up = sc.get("UserPreferences", {})
    notif = up.get("properties", {}).get("notifications", {})
    in_app = notif.get("properties", {}).get("inApp", {})
    out.append((
        "UserPreferences.notifications.inApp boolean default true",
        in_app.get("type") == "boolean" and in_app.get("default") is True,
        f"inApp={in_app!r}",
    ))
    # 4. ErrorResponse.details.items.properties.code
    er = sc.get("ErrorResponse", {})
    details = er.get("properties", {}).get("details", {})
    detail_code = details.get("items", {}).get("properties", {}).get("code", {})
    out.append((
        "ErrorResponse.details.items.properties.code string",
        detail_code.get("type") == "string",
        f"code={detail_code!r}",
    ))
    # 5. GET /orders status param enum has 'returned'
    paths = spec.get("paths", {})
    get_orders = paths.get("/orders", {}).get("get", {})
    status_param = param_by_name(get_orders.get("parameters"), "status")
    status_enum = (status_param or {}).get("schema", {}).get("enum", [])
    out.append((
        "GET /orders status enum includes returned",
        "returned" in status_enum and len(status_enum) >= 5,
        f"enum={status_enum!r}",
    ))
    # 6. GET /users 200 response has x-rate-limit: 100
    get_users = paths.get("/users", {}).get("get", {})
    resp_200 = get_users.get("responses", {}).get("200", {})
    out.append((
        "GET /users 200 x-rate-limit 100",
        resp_200.get("x-rate-limit") == 100,
        f"x-rate-limit={resp_200.get('x-rate-limit')!r}",
    ))
    return out


def _keys_sorted_recursive(obj: Any) -> tuple[bool, str]:
    """Check if all dict keys at every level are alphabetically sorted.
    Returns (all_sorted, first_violation_description).
    """
    if isinstance(obj, dict):
        keys = list(obj.keys())
        if keys != sorted(keys):
            return False, f"unsorted keys: {keys!r}"
        for v in obj.values():
            ok, detail = _keys_sorted_recursive(v)
            if not ok:
                return False, detail
    elif isinstance(obj, list):
        for item in obj:
            ok, detail = _keys_sorted_recursive(item)
            if not ok:
                return False, detail
    return True, "ok"


def check_eval_11(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    """Canonical key sorting at every level."""
    out: list[tuple[str, bool, str]] = []
    # 1. Top-level keys sorted
    top_keys = list(spec.keys())
    out.append((
        "Top-level keys sorted",
        top_keys == sorted(top_keys),
        f"keys={top_keys!r}",
    ))
    # 2. info keys sorted
    info_keys = list(spec.get("info", {}).keys())
    out.append((
        "info keys sorted",
        info_keys == sorted(info_keys),
        f"keys={info_keys!r}",
    ))
    # 3. paths keys sorted
    path_keys = list(spec.get("paths", {}).keys())
    out.append((
        "path keys sorted",
        path_keys == sorted(path_keys),
        f"keys={path_keys!r}",
    ))
    # 4. User schema keys sorted
    user_keys = list(schemas(spec).get("User", {}).keys())
    out.append((
        "User schema keys sorted",
        user_keys == sorted(user_keys),
        f"keys={user_keys!r}",
    ))
    # 5. Recursive check — all keys everywhere sorted
    all_sorted, detail = _keys_sorted_recursive(spec)
    out.append((
        "All keys at every level sorted",
        all_sorted,
        detail,
    ))
    # 6. Semantic equivalence — spot-check some values survived
    info = spec.get("info", {})
    user_props = schemas(spec).get("User", {}).get("properties", {})
    out.append((
        "Semantic equivalence (info.title + User.email.format)",
        info.get("title") == "Acme Commerce Platform API"
        and user_props.get("email", {}).get("format") == "email",
        f"title={info.get('title')!r}, email_fmt={user_props.get('email', {}).get('format')!r}",
    ))
    return out


def check_eval_12(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    """Schema deletion with referential integrity repair."""
    out: list[tuple[str, bool, str]] = []
    sc = schemas(spec)
    # 1. Dimensions removed
    out.append((
        "Dimensions schema removed",
        "Dimensions" not in sc,
        "still present" if "Dimensions" in sc else "ok",
    ))
    # 2. Product.dimensions inlined with width
    dims = sc.get("Product", {}).get("properties", {}).get("dimensions", {})
    out.append((
        "Product.dimensions has width inlined",
        "width" in dims.get("properties", {}),
        f"dimensions keys={list(dims.get('properties', {}).keys())!r}",
    ))
    # 3. Address removed
    out.append((
        "Address schema removed",
        "Address" not in sc,
        "still present" if "Address" in sc else "ok",
    ))
    # 4. Order.shippingAddress inlined with street
    ship = sc.get("Order", {}).get("properties", {}).get("shippingAddress", {})
    out.append((
        "Order.shippingAddress has street inlined",
        "street" in ship.get("properties", {}),
        f"shippingAddress keys={list(ship.get('properties', {}).keys())!r}",
    ))
    # 5. CreateOrderRequest.shippingAddress inlined
    cor_ship = sc.get("CreateOrderRequest", {}).get("properties", {}).get("shippingAddress", {})
    out.append((
        "CreateOrderRequest.shippingAddress has street inlined",
        "street" in cor_ship.get("properties", {}),
        f"keys={list(cor_ship.get('properties', {}).keys())!r}",
    ))
    # 6. UserPreferences removed
    out.append((
        "UserPreferences schema removed",
        "UserPreferences" not in sc,
        "still present" if "UserPreferences" in sc else "ok",
    ))
    # 7. User.preferences inlined with theme
    prefs = sc.get("User", {}).get("properties", {}).get("preferences", {})
    out.append((
        "User.preferences has theme inlined",
        "theme" in prefs.get("properties", {}),
        f"preferences keys={list(prefs.get('properties', {}).keys())!r}",
    ))
    # 8. UpdateUserRequest.preferences inlined
    up_prefs = sc.get("UpdateUserRequest", {}).get("properties", {}).get("preferences", {})
    out.append((
        "UpdateUserRequest.preferences has theme inlined",
        "theme" in up_prefs.get("properties", {}),
        f"keys={list(up_prefs.get('properties', {}).keys())!r}",
    ))
    # 9. No dangling $ref to deleted schemas
    def _has_deleted_ref(obj: Any) -> bool:
        deleted = {"Dimensions", "Address", "UserPreferences"}
        if isinstance(obj, dict):
            ref = obj.get("$ref", "")
            if isinstance(ref, str):
                for d in deleted:
                    if d in ref:
                        return True
            return any(_has_deleted_ref(v) for v in obj.values())
        if isinstance(obj, list):
            return any(_has_deleted_ref(v) for v in obj)
        return False

    out.append((
        "No dangling $ref to deleted schemas",
        not _has_deleted_ref(spec),
        "dangling ref found" if _has_deleted_ref(spec) else "ok",
    ))
    return out


def check_eval_13(spec: dict[str, Any], raw_text: str, fmt: str) -> list[tuple[str, bool, str]]:
    """Format-specific annotations + x-stability on GET endpoints."""
    out: list[tuple[str, bool, str]] = []
    paths = spec.get("paths", {})

    if fmt == "yaml":
        # Check for YAML comments in raw text
        out.append((
            "YAML comment: User Management before /users",
            "# --- User Management ---" in raw_text,
            "comment found" if "# --- User Management ---" in raw_text else "not found",
        ))
        out.append((
            "YAML comment: Product Catalog before /products",
            "# --- Product Catalog ---" in raw_text,
            "comment found" if "# --- Product Catalog ---" in raw_text else "not found",
        ))
        out.append((
            "YAML comment: Order Processing before /orders",
            "# --- Order Processing ---" in raw_text,
            "comment found" if "# --- Order Processing ---" in raw_text else "not found",
        ))
        out.append((
            "YAML comment: Schema Definitions before schemas",
            "# === Schema Definitions ===" in raw_text,
            "comment found" if "# === Schema Definitions ===" in raw_text else "not found",
        ))
    else:
        # Check for x-section-doc in JSON
        out.append((
            "JSON /users x-section-doc",
            paths.get("/users", {}).get("x-section-doc") == "User Management",
            f"got {paths.get('/users', {}).get('x-section-doc')!r}",
        ))
        out.append((
            "JSON /products x-section-doc",
            paths.get("/products", {}).get("x-section-doc") == "Product Catalog",
            f"got {paths.get('/products', {}).get('x-section-doc')!r}",
        ))
        out.append((
            "JSON /orders x-section-doc",
            paths.get("/orders", {}).get("x-section-doc") == "Order Processing",
            f"got {paths.get('/orders', {}).get('x-section-doc')!r}",
        ))
        out.append((
            "JSON components x-section-doc",
            spec.get("components", {}).get("x-section-doc") == "Schema Definitions",
            f"got {spec.get('components', {}).get('x-section-doc')!r}",
        ))

    # Check x-stability on all GET endpoints
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
        out.append((
            f"GET {path} x-stability stable",
            op.get("x-stability") == "stable",
            f"x-stability={op.get('x-stability')!r}",
        ))

    return out


def check_eval_14(spec: dict[str, Any]) -> list[tuple[str, bool, str]]:
    """Bidirectional format conversion — check semantic equivalence."""
    out: list[tuple[str, bool, str]] = []
    info = spec.get("info", {})
    # 1. info.title
    out.append((
        "info.title preserved",
        info.get("title") == "Acme Commerce Platform API",
        f"got {info.get('title')!r}",
    ))
    # 2. info.version
    out.append((
        "info.version preserved",
        info.get("version") == "2.0.0",
        f"got {info.get('version')!r}",
    ))
    # 3. All paths exist
    expected_paths = ["/users", "/users/{userId}", "/products", "/products/{productId}",
                      "/products/legacy", "/orders"]
    actual_paths = list(spec.get("paths", {}).keys())
    out.append((
        "All paths preserved",
        all(p in actual_paths for p in expected_paths),
        f"missing={[p for p in expected_paths if p not in actual_paths]!r}",
    ))
    # 4. All schemas exist
    expected_schemas = ["User", "Product", "Order", "OrderItem", "Address",
                        "Dimensions", "UserPreferences", "ErrorResponse"]
    sc = schemas(spec)
    out.append((
        "All schemas preserved",
        all(s in sc for s in expected_schemas),
        f"missing={[s for s in expected_schemas if s not in sc]!r}",
    ))
    # 5. User schema integrity
    user = sc.get("User", {})
    user_props = list(user.get("properties", {}).keys())
    out.append((
        "User properties preserved",
        "username" in user_props and "email" in user_props and "age" in user_props,
        f"properties={user_props!r}",
    ))
    user_req = user.get("required", [])
    out.append((
        "User required preserved",
        "id" in user_req and "username" in user_req and "email" in user_req,
        f"required={user_req!r}",
    ))
    # 6. Order.status enum
    order_status = sc.get("Order", {}).get("properties", {}).get("status", {})
    out.append((
        "Order.status enum preserved",
        order_status.get("enum") == ["pending", "confirmed", "in_transit", "fulfilled", "cancelled"],
        f"enum={order_status.get('enum')!r}",
    ))
    # 7. openapi version
    out.append((
        "openapi version preserved",
        spec.get("openapi") == "3.0.3",
        f"got {spec.get('openapi')!r}",
    ))
    return out


CHECKERS = {
    1: check_eval_1, 2: check_eval_2, 3: check_eval_3,
    4: check_eval_4, 5: check_eval_5, 6: check_eval_6,
    8: check_eval_8, 9: check_eval_9, 10: check_eval_10,
    11: check_eval_11, 12: check_eval_12, 14: check_eval_14,
}

# Evals 7 and 13 use special grading (raw text); they are not in CHECKERS.

CHECKS_PER_EVAL = {
    1: 6, 2: 6, 3: 6, 4: 10, 5: 7, 6: 12, 7: 11,
    8: 6, 9: 10, 10: 6, 11: 6, 12: 9, 13: 10, 14: 8,
}


def grade_file(path: Path, eval_id: int) -> dict[str, Any]:
    fn = CHECKERS[eval_id]
    nchecks = CHECKS_PER_EVAL[eval_id]
    try:
        spec = load_spec(path)
    except Exception as e:
        return {
            "path": str(path),
            "eval_id": eval_id,
            "error": str(e),
            "passed": 0,
            "failed": nchecks,
            "total": nchecks,
            "pass_rate": 0.0,
            "checks": [
                {
                    "name": "document parses (YAML/JSON)",
                    "passed": False,
                    "detail": str(e),
                }
            ],
        }
    checks = fn(spec)
    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    return {
        "path": str(path),
        "eval_id": eval_id,
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "pass_rate": passed / total if total else 0.0,
        "checks": [{"name": n, "passed": ok, "detail": d} for n, ok, d in checks],
    }


def grade_text_file(path: Path, eval_id: int, fmt: str = "") -> dict[str, Any]:
    """Grade evals that need raw text (eval 7 markdown, eval 13 format-specific annotations)."""
    nchecks = CHECKS_PER_EVAL[eval_id]
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "path": str(path),
            "eval_id": eval_id,
            "error": str(e),
            "passed": 0,
            "failed": nchecks,
            "total": nchecks,
            "pass_rate": 0.0,
            "checks": [{"name": "file readable", "passed": False, "detail": str(e)}],
        }
    if eval_id == 7:
        checks = check_eval_7(text)
    elif eval_id == 13:
        try:
            spec = load_spec(path)
        except Exception as e:
            return {
                "path": str(path),
                "eval_id": eval_id,
                "error": str(e),
                "passed": 0,
                "failed": nchecks,
                "total": nchecks,
                "pass_rate": 0.0,
                "checks": [{"name": "document parses", "passed": False, "detail": str(e)}],
            }
        checks = check_eval_13(spec, text, fmt)
    else:
        checks = []
    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    return {
        "path": str(path),
        "eval_id": eval_id,
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "pass_rate": passed / total if total else 0.0,
        "checks": [{"name": n, "passed": ok, "detail": d} for n, ok, d in checks],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "root",
        type=Path,
        help="Directory containing eval-N-yaml and eval-N-json subdirs",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    results: list[dict[str, Any]] = []
    all_evals = list(range(1, 15))
    for fmt in ("yaml", "json"):
        for eid in all_evals:
            sub = root / f"eval-{eid}-{fmt}"
            # Determine output file path based on eval type
            if eid == 7:
                out = sub / "output.md"
            elif eid == 14:
                # Bidirectional: yaml input -> json output, json input -> yaml output
                opposite = "json" if fmt == "yaml" else "yaml"
                out = sub / f"output.{opposite}"
            else:
                out = sub / f"output.{fmt}"
            if not out.is_file():
                results.append(
                    {
                        "path": str(out),
                        "eval_id": eid,
                        "format": fmt,
                        "error": "missing file",
                        "pass_rate": 0.0,
                    }
                )
                continue
            if eid in (7, 13):
                g = grade_text_file(out, eid, fmt=fmt)
            else:
                g = grade_file(out, eid)
            g["format"] = fmt
            results.append(g)

    passed = sum(
        r.get("passed", 0)
        for r in results
        if "passed" in r and "error" not in r
    )
    total = sum(r.get("total", 0) for r in results if "total" in r)
    yaml_rates = [r["pass_rate"] for r in results if r.get("format") == "yaml" and "pass_rate" in r]
    json_rates = [r["pass_rate"] for r in results if r.get("format") == "json" and "pass_rate" in r]
    summary = {
        "root": str(root),
        "assertions_passed": passed,
        "assertions_total": total,
        "overall_pass_rate": passed / total if total else 0.0,
        "yaml_mean_pass_rate": sum(yaml_rates) / len(yaml_rates) if yaml_rates else None,
        "json_mean_pass_rate": sum(json_rates) / len(json_rates) if json_rates else None,
        "runs": results,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
