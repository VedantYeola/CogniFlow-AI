import { useState, useEffect } from "react";
import { Authenticator, View, Flex, Heading, Button, Text, Card, Divider } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { fetchAuthSession } from "aws-amplify/auth";
import { FileUpload } from "./components/Fileupload";
import { AuditHistory } from "./components/AuditHistory";

function App() {
  const [userName, setUserName] = useState<string>("User");
  // Default tab is 'upload'
  const [activeTab, setActiveTab] = useState<string>("upload");

  useEffect(() => {
    async function getUserData() {
      try {
        const session = await fetchAuthSession();
        const idToken = session.tokens?.idToken?.payload;
        if (idToken) {
          const name = (idToken.name as string) || (idToken.given_name as string) || "User";
          setUserName(name);
        }
      } catch (err) {
        console.error("Session identity check failed:", err);
      }
    }
    getUserData();
  }, []);

  return (
    <Authenticator socialProviders={['google']}>
      {({ signOut }) => (
        <View className="App" backgroundColor="#f5f7fa" minHeight="100vh">
          {/* HEADER */}
          <Card variation="elevated" padding="1rem 2rem" borderRadius="0">
            <Flex justifyContent="space-between" alignItems="center">
              <Heading level={3} color="#3182ce">Smart Auditor</Heading>
              <Flex alignItems="center" gap="1rem">
                <Text fontWeight="bold">Hello, {userName}</Text>
                <Button variation="primary" size="small" onClick={signOut}>Sign Out</Button>
              </Flex>
            </Flex>
          </Card>

          {/* TAB NAVIGATION AREA */}
          <View maxWidth="1000px" margin="2rem auto 0 auto" padding="0 2rem">
            <Flex gap="1rem" marginBottom="1rem">
              <Button 
                variation={activeTab === "upload" ? "primary" : "link"} 
                onClick={() => setActiveTab("upload")}
              >
                Upload & Analyze
              </Button>
              <Button 
                variation={activeTab === "history" ? "primary" : "link"} 
                onClick={() => setActiveTab("history")}
              >
                Audit History
              </Button>
            </Flex>

            {/* CONDITIONAL RENDERING: Shows only the selected "Tab" */}
            <Card variation="elevated" padding="2rem">
              {activeTab === "upload" ? (
                <View>
                  <Heading level={4} marginBottom="1rem">Analyze New Receipt</Heading>
                  <Divider marginBottom="1.5rem" />
                  <FileUpload />
                </View>
              ) : (
                <View>
                  <Heading level={4} marginBottom="1rem">Your Audit History</Heading>
                  <Divider marginBottom="1.5rem" />
                  <AuditHistory />
                </View>
              )}
            </Card>
          </View>
        </View>
      )}
    </Authenticator>
  );
}

export default App;