package lk.ac.mrt.fit.library_api.controller;
import java.util.List;
import jakarta.validation.Valid;
import lk.ac.mrt.fit.library_api.model.Book;
import lk.ac.mrt.fit.library_api.service.BookService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
@Tag(name = "Books", description = "Create, read, update and delete books")
@RestController
@RequestMapping("/api/books")
public class BookController {
 private final BookService bookService;
 public BookController(BookService bookService) { this.bookService = bookService; }
 @GetMapping
 public List<Book> getAllBooks() { return bookService.getAllBooks(); }
 @GetMapping("/{id}")
 public ResponseEntity<Book> getBookById(@PathVariable Long id) {
  return bookService.getBookById(id).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
 }
 @Operation(summary = "Create a book", description = "Adds a book and returns it with its new id.")
 @ApiResponse(responseCode = "201", description = "Book created")
 @ApiResponse(responseCode = "400", description = "Invalid input")
 @PostMapping
 public ResponseEntity<Book> createBook(@Valid @RequestBody Book book) {
  return ResponseEntity.status(HttpStatus.CREATED).body(bookService.createBook(book));
 }
 @PutMapping("/{id}")
 public ResponseEntity<Book> updateBook(@PathVariable Long id, @Valid @RequestBody Book book) {
  return bookService.updateBook(id, book).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
 }
 @DeleteMapping("/{id}")
 public ResponseEntity<Void> deleteBook(@PathVariable Long id) {
  return bookService.deleteBook(id) ? ResponseEntity.noContent().build() : ResponseEntity.notFound().build();
 }
}
