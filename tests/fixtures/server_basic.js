#!/usr/bin/env node
/**
 * Simple MCP server in Node.js
 */

const { Server } = require('@modelcontextprotocol/server');

const server = new Server("test-server");

server.addTool("add", {
  description: "Add two numbers",
  inputSchema: {
    type: "object",
    properties: {
      a: { type: "number" },
      b: { type: "number" }
    }
  }
}, async (args) => {
  return args.a + args.b;
});

server.run();
