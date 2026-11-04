package lk.ac.mrt.fit.library_api.model;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.PositiveOrZero;
@Entity
public class Book {
 @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
 private Long id;
 @NotBlank private String title;
 @NotBlank private String author;
 private String isbn;
 @PositiveOrZero private Double price;
 public Book() {}
 public Long getId() { return id; }
 public void setId(Long id) { this.id = id; }
 public String getTitle() { return title; }
 public void setTitle(String title) { this.title = title; }
 public String getAuthor() { return author; }
 public void setAuthor(String author) { this.author = author; }
 public String getIsbn() { return isbn; }
 public void setIsbn(String isbn) { this.isbn = isbn; }
 public Double getPrice() { return price; }
 public void setPrice(Double price) { this.price = price; }
}
