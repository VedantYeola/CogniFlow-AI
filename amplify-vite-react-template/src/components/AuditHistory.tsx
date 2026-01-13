import { useState, useEffect } from 'react';
import { Table, TableHead, TableRow, TableCell, TableBody, Badge, Text, Loader, Button, Card, Flex } from "@aws-amplify/ui-react";
import { list, remove, getUrl } from 'aws-amplify/storage';
import { get } from 'aws-amplify/api';

// 1. Define an Interface to fix the "spread" error
interface MergedReport {
  path: string;
  finalAmount?: string;
  category?: string;
  summary?: string;
  violation?: boolean;
  status?: string;
}

export function AuditHistory() {
  const [reports, setReports] = useState<MergedReport[]>([]); // Use the interface here
  const [loading, setLoading] = useState(true);

  const handleView = async (path: string) => {
    try {
      const linkToStorageFile = await getUrl({ 
        path: path,
        options: { validateObjectExistence: true, expiresIn: 900 }
      });
      window.open(linkToStorageFile.url.toString(), '_blank', 'noreferrer');
    } catch (error) {
      console.error("Error generating view link:", error);
      alert("Could not open file.");
    }
  };

  const fetchHistory = async () => {
    try {
      // Fetch S3 files from the private path
      const s3Result = await list({ 
        path: ({identityId}) => `private/${identityId}/` 
      });

      const mergedData = await Promise.all(
        s3Result.items.map(async (file): Promise<MergedReport> => {
          try {
            const restOperation = get({
              apiName: 'auditApi', // Ensure this matches amplifyconfiguration.json
              path: '/audit',
              options: {
                queryParams: { userId: file.path }
              }
            });

            const { body } = await restOperation.response; // Amplify v6 stream response
            const auditData = await body.json() as any;
            
            // 2. Build the object manually to avoid Type errors
            return { 
              path: file.path,
              finalAmount: auditData?.finalAmount,
              category: auditData?.category || "Pending",
              summary: auditData?.summary || "AI is auditing your receipt...",
              violation: auditData?.violation || false,
              status: auditData?.status || "PROCESSING"
            };
          } catch (e) {
            // Fallback for missing records
            return { 
              path: file.path, 
              status: "PROCESSING", 
              summary: "Waiting for AI results..." 
            };
          }
        })
      );
      setReports(mergedData);
    } catch (error) { 
      console.error("S3 List Error:", error); 
    } finally { 
      setLoading(false); 
    }
  };

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 7000); // Polling for AI updates
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (path: string) => {
    if (!window.confirm("Delete record?")) return;
    try {
      await remove({ path });
      setReports(prev => prev.filter(item => item.path !== path));
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  if (loading && reports.length === 0) return <Flex justifyContent="center" padding="2rem"><Loader size="large" /></Flex>;

  return (
    <Card variation="elevated" padding="0" marginTop="1rem">
      <Table highlightOnHover variation="striped">
        <TableHead>
          <TableRow>
            <TableCell as="th">File Name</TableCell>
            <TableCell as="th">Amount</TableCell>
            <TableCell as="th">AI Category</TableCell>
            <TableCell as="th">Audit Summary</TableCell>
            <TableCell as="th">Action</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {reports.length === 0 ? (
            <TableRow><TableCell colSpan={5} textAlign="center" padding="2rem">No receipts found.</TableCell></TableRow>
          ) : (
            reports.map((report) => (
              <TableRow key={report.path}>
                <TableCell>{report.path.split('/').pop()}</TableCell>
                <TableCell fontWeight="bold">
                  {report.finalAmount ? `$${report.finalAmount}` : "Scanning..."}
                </TableCell>
                <TableCell>
                  <Badge variation={report.violation ? "error" : "success"}>
                    {report.category || "Pending"}
                  </Badge>
                </TableCell>
                <TableCell><Text fontSize="0.9rem" color="#666">{report.summary}</Text></TableCell>
                <TableCell>
                  <Flex gap="small">
                    <Button variation="link" size="small" onClick={() => handleView(report.path)}>View</Button>
                    <Button variation="link" size="small" colorTheme="error" onClick={() => handleDelete(report.path)}>Delete</Button>
                  </Flex>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}