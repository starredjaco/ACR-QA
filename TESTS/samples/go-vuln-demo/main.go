package main

import (
	"crypto/md5"
	"database/sql"
	"fmt"
	"net/http"
	"os/exec"
)

// G101: hardcoded credentials
const apiKey = "sk_live_51H8xQk2eZvKYlo3hardcodedsecret"

// G401/G501: weak crypto (MD5)
func hashPassword(p string) string {
	h := md5.Sum([]byte(p))
	return fmt.Sprintf("%x", h)
}

// G204: command injection from user input
func ping(host string) {
	out, _ := exec.Command("sh", "-c", "ping -c1 "+host).Output()
	fmt.Println(string(out))
}

// G202: SQL injection via string concatenation
func getUser(db *sql.DB, name string) {
	q := "SELECT * FROM users WHERE name = '" + name + "'"
	db.Query(q)
}

func handler(w http.ResponseWriter, r *http.Request) {
	host := r.URL.Query().Get("host")
	ping(host)
	fmt.Fprintf(w, "hashed: %s key: %s", hashPassword(host), apiKey)
}

func main() {
	http.HandleFunc("/", handler)
	http.ListenAndServe(":8080", nil)
}
