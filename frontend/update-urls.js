const fs = require('fs');
const path = require('path');

// List of files to update
const filesToUpdate = [
  'src/components/DailyPostPage.tsx',
  'src/components/DMAutomationPage.tsx',
  'src/components/AdminDashboard.tsx',
  'src/utils/browserCloseDetector.ts'
];

// Replacement patterns
const replacements = [
  {
    from: /const token = authService\.getToken\(\);\s*const response = await axios\.get\(`https:\/\/wdyautomation\.shop\/api\/([^`]+)`, \{\s*headers: \{\s*Authorization: `Bearer \$\{token\}`\s*\}\s*\}\);/g,
    to: "const response = await axios.get(getApiUrl('/$1'), {\n        headers: getApiHeaders()\n      });"
  },
  {
    from: /const token = authService\.getToken\(\);\s*const response = await axios\.post\('https:\/\/wdyautomation\.shop\/api\/([^']+)', ([^,]+), \{\s*headers: \{\s*'Content-Type': 'multipart\/form-data',\s*Authorization: `Bearer \$\{token\}`\s*\}\s*\}\);/g,
    to: "const response = await axios.post(getApiUrl('/$1'), $2, {\n        headers: getMultipartHeaders()\n      });"
  },
  {
    from: /const token = authService\.getToken\(\);\s*await axios\.post\(`https:\/\/wdyautomation\.shop\/api\/([^`]+)`, ([^,]+), \{\s*headers: \{\s*Authorization: `Bearer \$\{token\}`\s*\}\s*\}\);/g,
    to: "await axios.post(getApiUrl('/$1'), $2, {\n        headers: getApiHeaders()\n      });"
  },
  {
    from: /https:\/\/wdyautomation\.shop\/api\//g,
    to: "getApiUrl('/"
  },
  {
    from: /getApiUrl\('\/([^']+)'\)/g,
    to: "getApiUrl('/$1')"
  }
];

// Process each file
filesToUpdate.forEach(filePath => {
  const fullPath = path.join(__dirname, filePath);
  
  if (fs.existsSync(fullPath)) {
    let content = fs.readFileSync(fullPath, 'utf8');
    
    // Add import if not present
    if (!content.includes('getApiUrl') && content.includes('wdyautomation.shop')) {
      const importRegex = /import.*from.*authService.*;\n/;
      content = content.replace(importRegex, match => 
        match + "import { getApiUrl, getApiHeaders, getMultipartHeaders } from '../utils/apiUtils';\n"
      );
    }
    
    // Apply replacements
    replacements.forEach(replacement => {
      content = content.replace(replacement.from, replacement.to);
    });
    
    // Fix any remaining URLs
    content = content.replace(/https:\/\/wdyautomation\.shop\/api\/([^'"`,\s\)]+)/g, "' + getApiUrl('/$1");
    
    fs.writeFileSync(fullPath, content);
    console.log(`Updated ${filePath}`);
  } else {
    console.log(`File not found: ${filePath}`);
  }
});

console.log('URL updates completed!');
