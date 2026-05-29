import java.io.*;
import java.net.*;
import java.util.*;

/**
 * ATM银行服务器 - Java端
 * 端口：默认2525，可通过命令行参数指定
 */
public class ATMserver {
    
    // 会话状态常量
    private static final int STATE_INIT = 0;              // 初始状态
    private static final int STATE_AUTH_REQUIRED = 1;     // 需要认证
    private static final int STATE_LOGGED_IN = 2;         // 已登录
    
    // 存储数据（内存）
    private static Map<String, String> userMap = new HashMap<>();   // 卡号->密码
    private static Map<String, Double> balanceMap = new HashMap<>(); // 卡号->余额
    
    // 默认端口
    private static final int DEFAULT_PORT = 17685;
    private static final int MIN_PORT = 1024;
    private static final int MAX_PORT = 65535;
    
    public static void main(String[] args) {
        // 1. 加载数据文件
        loadUserData();
        
        // 2. 获取端口参数
        int port = DEFAULT_PORT;
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);
                // 处理0721这种写法
                if (args[0].startsWith("0") && args[0].length() > 1) {
                    port = Integer.parseInt(args[0]);
                }
            } catch (NumberFormatException e) {
                System.out.println("端口号格式错误！使用默认端口2525");
                port = DEFAULT_PORT;
            }
        }
        
        // 3. 端口合法性检查
        if (port < MIN_PORT || port > MAX_PORT) {
            System.out.println("端口号必须在" + MIN_PORT + "~" + MAX_PORT + "之间！使用默认端口2525");
            port = DEFAULT_PORT;
        }
        
        System.out.println("ATM服务器启动，监听端口：" + port);
        
        // 4. 创建服务器Socket
        ServerSocket serverSocket = null;
        try {
            serverSocket = new ServerSocket(port);
        } catch (IOException e) {
            System.out.println("服务器启动失败，端口可能已被占用！");
            e.printStackTrace();
            return;
        }
        
        // 5. 循环接受客户端连接
        while (true) {
            try {
                Socket clientSocket = serverSocket.accept();
                System.out.println("新连接：" + clientSocket.getRemoteSocketAddress());
                
                // 为每个客户端创建独立线程处理
                new Thread(new ClientHandler(clientSocket)).start();
                
            } catch (IOException e) {
                System.out.println("接受连接失败：" + e.getMessage());
                break;
            }
        }
        
        try {
            serverSocket.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    
    // === 数据加载方法 ===
    private static void loadUserData() {
        // 加载用户信息
        loadFile("users.txt", "users");
        // 加载余额信息
        loadFile("balances.txt", "balances");
        System.out.println("用户数据加载完成！");
    }
    
    private static void loadFile(String filename, String type) {
        BufferedReader reader = null;
        try {
            reader = new BufferedReader(new FileReader(filename));
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.trim().split("\\s+");
                if (parts.length >= 2) {
                    String card = parts[0];
                    if (type.equals("users")) {
                        userMap.put(card, parts[1]);
                    } else {
                        balanceMap.put(card, Double.parseDouble(parts[1]));
                    }
                }
            }
        } catch (IOException e) {
            System.out.println("加载文件" + filename + "失败：" + e.getMessage());
        } finally {
            try {
                if (reader != null) reader.close();
            } catch (IOException e) {}
        }
    }
    
    // === 客户端处理线程 ===
    static class ClientHandler implements Runnable {
        private Socket socket;
        private int state = STATE_INIT;  // 会话状态
        private String currentCard = null;  // 当前会话卡号
        
        public ClientHandler(Socket socket) {
            this.socket = socket;
        }
        
        @Override
        public void run() {
            BufferedReader in = null;
            PrintWriter out = null;
            try {
                in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                out = new PrintWriter(socket.getOutputStream(), true);
                
                String userRequest;
                
                while ((userRequest = in.readLine()) != null) {
                    System.out.println("收到" + (currentCard != null ? currentCard : "新") + "账户的请求：" + userRequest);
                    
                    // 解析命令
                    String[] args = userRequest.trim().split("\\s+");
                    String command = args[0].toUpperCase();
                    
                    String response = null;
                    
                    // 根据命令处理
                    switch (command) {
                        case "HELO":
                            response = handleHELO(args);
                            break;
                            
                        case "PASS":
                            response = handlePASS(args);
                            break;
                            
                        case "BALA":
                            response = handleBALA();
                            break;
                            
                        case "WDRA":
                            response = handleWDRA(args);
                            break;
                            
                        case "QUIT":
                            response = handleQUIT();
                            break;
                            
                        default:
                            response = "401 ERROR!";  // 未知命令
                    }
                    
                    out.println(response);
                    System.out.println("发送" + (currentCard != null ? currentCard : "新") + "账户的响应：" + response);

                    if (command.equals("QUIT")) {
                        closeSession();
                    }
                }
                
            } catch (IOException e) {
                System.out.println("与客户端通信失败：" + e.getMessage());
            } finally {
                try {
                    socket.close();
                    System.out.println("连接已关闭");
                } catch (IOException e) {}
            }
        }
        
        // === 各命令处理函数 ===
        
        private String handleHELO(String[] args) {
            if (args.length < 2) {
                return "401 ERROR!";
            }
            currentCard = args[1];
            state = STATE_AUTH_REQUIRED;
            return "500 AUTH REQUIRE";
        }
        
        private String handlePASS(String[] args) {
            if (state != STATE_AUTH_REQUIRED || args.length < 2) {
                return "401 ERROR!";
            }
            
            String password = args[1];
            String storedPassword = userMap.get(currentCard);
            
            if (storedPassword != null && storedPassword.equals(password)) {
                state = STATE_LOGGED_IN;
                return "525 OK!";
            } else {
                return "401 ERROR!";
            }
        }
        
        private String handleBALA() {
            if (state != STATE_LOGGED_IN) {
                return "401 ERROR!";
            }
            
            Double balance = balanceMap.get(currentCard);
            if (balance != null) {
                return "AMNT:" + String.format("%.2f", balance);
            } else {
                return "401 ERROR!";
            }
        }
        
        private String handleWDRA(String[] args) {
            if (state != STATE_LOGGED_IN || args.length < 2) {
                return "401 ERROR!";
            }
            
            double amount;
            try {
                amount = Double.parseDouble(args[1]);
            } catch (NumberFormatException e) {
                return "401 ERROR!";
            }
            
            Double balance = balanceMap.get(currentCard);
            if (balance == null || balance < amount) {
                return "401 ERROR!";
            }
            
            // 更新余额
            double newBalance = balance - amount;
            balanceMap.put(currentCard, newBalance);
            
            // 写入文件（持久化）
            saveBalances();
            
            return "525 OK!";
        }
        
        private String handleQUIT() {
            if (state == STATE_LOGGED_IN || state == STATE_AUTH_REQUIRED) {
                return "BYE";
            }
            return "BYE";
        }
        
        private void closeSession() {
            state = STATE_INIT;
            currentCard = null;
        }
        
        private void saveBalances() {
            try (PrintWriter writer = new PrintWriter(new FileWriter("balances.txt"))) {
                for (Map.Entry<String, Double> entry : balanceMap.entrySet()) {
                    writer.println(entry.getKey() + " " + entry.getValue());
                }
            } catch (IOException e) {
                System.out.println("保存余额失败：" + e.getMessage());
            }
        }
    }
}
