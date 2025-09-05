#include <drogon/drogon.h>

int main() {
    // Register a handler for the root path "/"
    drogon::app().registerHandler(
        "/",
        [](const drogon::HttpRequestPtr &request,
           std::function<void(const drogon::HttpResponsePtr &)> &&callback) {
            // Create a new HTTP response
            auto resp = drogon::HttpResponse::newHttpResponse();
            // Set the response body to "Hello World"
            resp->setBody("Hello World");
            // Send the response back to the client
            callback(resp);
        });

    // Add a listener to bind the server to all available network interfaces on port 8080
    drogon::app().addListener("0.0.0.0", 8080);

    // Set the number of worker threads for the application
    drogon::app().setNumThreads(3);

    // Run the Drogon application, starting the main event loop and worker threads
    drogon::app().run();

    return 0;
}