package com.example.orderservice.repository;
import com.example.orderservice.domain.Order;
import org.springframework.data.jpa.repository.JpaRepository;
public interface OrderRepository extends JpaRepository<Order, String> {}