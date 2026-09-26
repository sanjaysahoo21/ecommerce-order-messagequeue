package com.example.shippingservice.config;
import org.springframework.amqp.core.*;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {
    @Bean
    public TopicExchange exchange() { return new TopicExchange("order_exchange", true, false); }
    @Bean
    public Queue shippingQueue() { return new Queue("shipping.queue", true); }
    @Bean
    public Binding binding() { return BindingBuilder.bind(shippingQueue()).to(exchange()).with("inventory.reserved"); }
    @Bean
    public MessageConverter converter() { return new Jackson2JsonMessageConverter(); }
}