package lk.ac.mrt.fit.library_api.repository;
import lk.ac.mrt.fit.library_api.model.Book;
import org.springframework.data.jpa.repository.JpaRepository;
public interface BookRepository extends JpaRepository<Book, Long> {}
