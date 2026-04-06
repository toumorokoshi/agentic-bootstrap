## Address

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| city | string | Yes | - |
| country | string | Yes | ISO 3166-1 alpha-2 country code. |
| postalCode | string | No | - |
| state | string | No | State or province. |
| street | string | Yes | Street address including number. |

## CreateOrderRequest

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| items | array of object | Yes | Minimum 1 item. |
| notes | string | No | Maximum 500 characters. |
| shippingAddress | Address | Yes | - |

## CreateUserRequest

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| email | string | Yes | The user's email address. Must be unique. |
| firstName | string | No | Optional first name. |
| lastName | string | No | Optional last name. |
| password | string | Yes | The user's password. Must be at least 8 characters. |
| username | string | Yes | Desired username. Must be alphanumeric with underscores or hyphens. |

## Dimensions

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| depth | number | No | Depth in centimeters. |
| height | number | No | Height in centimeters. |
| weight | number | No | Weight in kilograms. |
| width | number | No | Width in centimeters. |

## ErrorResponse

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| code | string | Yes | Machine-readable error code. |
| details | array of object | No | - |
| message | string | Yes | Human-readable error description. |

## Order

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| id | string | Yes | The unique identifier of the order. |
| items | array of OrderItem | Yes | Minimum 1 item. |
| notes | string | No | Optional notes from the customer. |
| shippingAddress | Address | No | - |
| status | string | Yes | Current status of the order. |
| total | number | Yes | Total cost of the order in USD. |
| userId | string | Yes | The ID of the user who placed the order. |

## OrderItem

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| productId | string | Yes | The ID of the product ordered. |
| quantity | number | Yes | Number of units ordered. |
| unitPrice | number | No | Price per unit at time of order. |

## OrderListResponse

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| data | array of Order | No | - |
| total | integer | No | - |

## Product

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| category | string | Yes | The product category. |
| description | string | No | Detailed product description. |
| dimensions | Dimensions | No | - |
| id | string | Yes | The globally unique identifier of the product. |
| images | array of string | No | Product image URLs. |
| name | string | Yes | Display name of the product. |
| price | number | Yes | Unit price in USD. |
| stock | integer | Yes | Number of units currently in stock. |
| tags | array of string | No | Searchable tags associated with the product. |

## ProductListResponse

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| data | array of Product | No | - |
| total | integer | No | - |

## UpdateUserRequest

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| firstName | string | No | - |
| lastName | string | No | - |
| middleName | string | No | - |
| preferences | UserPreferences | No | - |

## User

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| age | number | Yes | The user's age in years. |
| createdAt | string | Yes | The date and time the user was created. |
| email | string | Yes | The user's email address. |
| firstName | string | No | The user's first name. |
| id | string | Yes | The unique identifier of the user. |
| lastName | string | No | The user's last name. |
| metadata | object | No | Arbitrary key-value metadata attached to the user. |
| middleName | string | No | The user's middle name, if any. |
| preferences | UserPreferences | No | - |
| role | string | Yes | The user's role in the system. |
| username | string | Yes | The user's chosen display name. |

## UserListResponse

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| data | array of User | No | - |
| limit | integer | No | - |
| offset | integer | No | - |
| total | integer | No | Total number of users matching the query. |

## UserPreferences

No description.

| Field | Type | Required | Description |
|---|---|---|---|
| language | string | No | IETF BCP 47 language tag. |
| notifications | object | No | Contains properties email, sms, push. |
| theme | string | No | Default: "system". |
