# Domain Model Test Examples

Reference file for comprehensive domain model testing patterns.

## Value Object Tests

```python
import pytest
from decimal import Decimal
from myproject.domain.model import Money, Address, DateRange


class TestMoney:
    """Value object tests for Money."""

    def test_money_equality(self):
        """Two Money with same value are equal."""
        assert Money(Decimal("10.00")) == Money(Decimal("10.00"))

    def test_money_inequality(self):
        """Different amounts are not equal."""
        assert Money(Decimal("10.00")) != Money(Decimal("20.00"))

    def test_money_addition(self):
        total = Money(Decimal("10.00")) + Money(Decimal("5.00"))
        assert total == Money(Decimal("15.00"))

    def test_cannot_add_different_currencies(self):
        with pytest.raises(ValueError, match="Cannot add"):
            Money(Decimal("10"), "USD") + Money(Decimal("5"), "EUR")

    def test_money_multiplication(self):
        result = Money(Decimal("10.00")) * 3
        assert result == Money(Decimal("30.00"))

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            Money(Decimal("-5"))


class TestDateRange:
    """Value object tests for DateRange."""

    def test_contains_date_within_range(self):
        range_ = DateRange(date(2024, 1, 1), date(2024, 12, 31))
        assert range_.contains(date(2024, 6, 15))

    def test_excludes_date_outside_range(self):
        range_ = DateRange(date(2024, 1, 1), date(2024, 12, 31))
        assert not range_.contains(date(2025, 1, 1))

    def test_invalid_range_raises(self):
        with pytest.raises(ValueError, match="End date must be after"):
            DateRange(date(2024, 12, 31), date(2024, 1, 1))

    def test_calculates_days_in_range(self):
        range_ = DateRange(date(2024, 1, 1), date(2024, 1, 10))
        assert range_.days == 9
```

## Entity Tests

```python
class TestCustomer:
    """Entity tests for Customer."""

    def test_customers_equal_by_id(self):
        """Two customers with same ID are equal."""
        customer1 = Customer(id="cust-1", name="Alice", email="alice@example.com")
        customer2 = Customer(id="cust-1", name="Alice Smith", email="alice2@example.com")
        assert customer1 == customer2

    def test_customers_not_equal_by_attributes(self):
        """Different IDs means different customers."""
        customer1 = Customer(id="cust-1", name="Alice", email="alice@example.com")
        customer2 = Customer(id="cust-2", name="Alice", email="alice@example.com")
        assert customer1 != customer2

    def test_can_update_address(self):
        customer = Customer(id="cust-1", name="Alice", email="alice@example.com")
        new_address = Address(street="123 Main", city="NYC", state="NY", postal_code="10001")

        customer.update_address(new_address)

        assert customer.address == new_address

    def test_customers_hashable_for_sets(self):
        customer = Customer(id="cust-1", name="Alice", email="alice@example.com")
        customer_set = {customer}
        assert customer in customer_set
```

## Aggregate Tests

```python
class TestOrder:
    """Aggregate tests for Order."""

    def test_can_add_line_to_order(self):
        order = Order(id="order-1", customer_id="cust-1")
        product = Product(sku="LAMP", name="Desk Lamp", price=Money(Decimal("25")))

        order.add_line(product, quantity=2)

        assert len(order.lines) == 1
        assert order.lines[0].quantity == 2

    def test_adding_same_product_increases_quantity(self):
        order = Order(id="order-1", customer_id="cust-1")
        product = Product(sku="LAMP", name="Desk Lamp", price=Money(Decimal("25")))

        order.add_line(product, quantity=2)
        order.add_line(product, quantity=3)

        assert len(order.lines) == 1
        assert order.lines[0].quantity == 5

    def test_cannot_exceed_max_lines(self):
        order = Order(id="order-1", customer_id="cust-1")

        for i in range(Order.MAX_LINES):
            order.add_line(
                Product(sku=f"SKU-{i}", name=f"Product {i}", price=Money(Decimal("10"))),
                quantity=1,
            )

        with pytest.raises(OrderTooLarge):
            order.add_line(
                Product(sku="EXTRA", name="One Too Many", price=Money(Decimal("10"))),
                quantity=1,
            )

    def test_cannot_add_zero_quantity(self):
        order = Order(id="order-1", customer_id="cust-1")
        product = Product(sku="LAMP", name="Lamp", price=Money(Decimal("25")))

        with pytest.raises(InvalidQuantity):
            order.add_line(product, quantity=0)

    def test_remove_line_from_order(self):
        order = Order(id="order-1", customer_id="cust-1")
        order.add_line(Product(sku="LAMP", name="Lamp", price=Money(Decimal("25"))), 1)
        order.add_line(Product(sku="DESK", name="Desk", price=Money(Decimal("100"))), 1)

        order.remove_line("LAMP")

        assert len(order.lines) == 1
        assert order.lines[0].sku == "DESK"

    def test_calculate_order_total(self):
        order = Order(id="order-1", customer_id="cust-1")
        order.add_line(Product(sku="LAMP", name="Lamp", price=Money(Decimal("25"))), 2)
        order.add_line(Product(sku="DESK", name="Desk", price=Money(Decimal("100"))), 1)

        assert order.total == Money(Decimal("150"))

    def test_empty_order_total_is_zero(self):
        order = Order(id="order-1", customer_id="cust-1")
        assert order.total == Money(Decimal("0"))


class TestOrderStatusTransitions:
    """Tests for order status state machine."""

    def test_confirm_order_changes_status(self):
        order = Order(id="order-1", customer_id="cust-1")
        order.add_line(Product(sku="LAMP", name="Lamp", price=Money(Decimal("25"))), 1)

        order.confirm()

        assert order.status == "confirmed"

    def test_confirm_raises_event(self):
        order = Order(id="order-1", customer_id="cust-1")
        order.add_line(Product(sku="LAMP", name="Lamp", price=Money(Decimal("25"))), 1)

        order.confirm()

        assert len(order.events) == 1
        assert isinstance(order.events[0], OrderConfirmed)

    def test_cannot_confirm_empty_order(self):
        order = Order(id="order-1", customer_id="cust-1")

        with pytest.raises(EmptyOrder):
            order.confirm()

    def test_cannot_confirm_already_confirmed(self):
        order = Order(id="order-1", customer_id="cust-1")
        order.add_line(Product(sku="LAMP", name="Lamp", price=Money(Decimal("25"))), 1)
        order.confirm()

        with pytest.raises(InvalidStatusTransition):
            order.confirm()

    def test_can_cancel_pending_order(self):
        order = Order(id="order-1", customer_id="cust-1")

        order.cancel()

        assert order.status == "cancelled"

    def test_cannot_cancel_shipped_order(self):
        order = Order(id="order-1", customer_id="cust-1", status="shipped")

        with pytest.raises(InvalidStatusTransition):
            order.cancel()
```

## Domain Service Tests

```python
class TestAllocateService:
    """Tests for the allocate domain service."""

    def test_prefers_earlier_batches(self):
        earliest = Batch("batch-001", "LAMP", 10, eta=today)
        medium = Batch("batch-002", "LAMP", 10, eta=tomorrow)
        latest = Batch("batch-003", "LAMP", 10, eta=next_week)

        line = OrderLine("order-1", "LAMP", 5)

        allocate(line, [medium, earliest, latest])

        assert earliest.available_quantity == 5
        assert medium.available_quantity == 10
        assert latest.available_quantity == 10

    def test_prefers_warehouse_stock_to_shipments(self):
        in_stock = Batch("batch-001", "LAMP", 10, eta=None)  # No ETA = in stock
        shipment = Batch("batch-002", "LAMP", 10, eta=tomorrow)

        line = OrderLine("order-1", "LAMP", 5)

        allocate(line, [shipment, in_stock])

        assert in_stock.available_quantity == 5
        assert shipment.available_quantity == 10

    def test_returns_allocated_batch_ref(self):
        batch = Batch("batch-001", "LAMP", 10, eta=None)
        line = OrderLine("order-1", "LAMP", 5)

        result = allocate(line, [batch])

        assert result == "batch-001"

    def test_raises_out_of_stock(self):
        batch = Batch("batch-001", "LAMP", 5, eta=None)
        line = OrderLine("order-1", "LAMP", 10)

        with pytest.raises(OutOfStock):
            allocate(line, [batch])
```
